"""Text processing utilities for chunking and preprocessing."""

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChunkMetadata:
    """Metadata for a text chunk."""

    chunk_index: int
    start_char: int
    end_char: int
    token_count: int
    sentence_count: int
    has_title: bool
    quality_score: float
    content_type: str  # 'paragraph', 'list', 'title', 'mixed'


class TextProcessor:
    """Service for processing and chunking text content."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

        # Compile regex patterns for better performance
        self.sentence_pattern = re.compile(r"[.!?]+\s+")
        self.title_pattern = re.compile(
            r"^(?:#{1,6}\s+|[A-Z][^.!?]*:?\s*$)", re.MULTILINE
        )
        self.list_pattern = re.compile(r"^\s*[-*•]\s+|^\s*\d+\.\s+", re.MULTILINE)

    async def chunk_text(self, text: str, preserve_structure: bool = True) -> list[str]:
        """Split text into chunks with optional structure preservation."""

        if not text.strip():
            return []

        # Clean the text first
        cleaned_text = self._clean_text(text)

        if preserve_structure:
            return await self._semantic_chunking(cleaned_text)
        else:
            return await self._sliding_window_chunking(cleaned_text)

    async def chunk_text_with_metadata(
        self, text: str, preserve_structure: bool = True
    ) -> list[tuple[str, ChunkMetadata]]:
        """Split text into chunks and return with detailed metadata."""

        if not text.strip():
            return []

        cleaned_text = self._clean_text(text)

        if preserve_structure:
            return await self._semantic_chunking_with_metadata(cleaned_text)
        else:
            return await self._sliding_window_chunking_with_metadata(cleaned_text)

    async def _semantic_chunking(self, text: str) -> list[str]:
        """Chunk text while preserving semantic structure."""
        chunks_with_metadata = await self._semantic_chunking_with_metadata(text)
        return [chunk for chunk, _ in chunks_with_metadata]

    async def _semantic_chunking_with_metadata(
        self, text: str
    ) -> list[tuple[str, ChunkMetadata]]:
        """Chunk text while preserving semantic structure and return metadata."""

        chunks = []

        # Detect document structure
        sections = self._identify_sections(text)

        current_chunk = ""
        current_start = 0
        chunk_index = 0

        for section in sections:
            section_text = section["text"].strip()
            if not section_text:
                continue

            section_size = len(section_text)
            current_size = len(current_chunk)

            # Check if adding this section would exceed chunk size
            if current_size + section_size > self.chunk_size and current_chunk:
                # Finalize current chunk
                chunk_metadata = self._create_chunk_metadata(
                    current_chunk,
                    chunk_index,
                    current_start,
                    current_start + len(current_chunk),
                )
                chunks.append((current_chunk.strip(), chunk_metadata))
                chunk_index += 1

                # Start new chunk with smart overlap
                overlap_text = self._get_semantic_overlap(current_chunk, section_text)
                current_chunk = (
                    overlap_text + "\n\n" + section_text
                    if overlap_text
                    else section_text
                )
                current_start = (
                    section["start"] - len(overlap_text)
                    if overlap_text
                    else section["start"]
                )
            else:
                # Add section to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + section_text
                else:
                    current_chunk = section_text
                    current_start = section["start"]

        # Handle the last chunk
        if current_chunk.strip():
            chunk_metadata = self._create_chunk_metadata(
                current_chunk,
                chunk_index,
                current_start,
                current_start + len(current_chunk),
            )
            chunks.append((current_chunk.strip(), chunk_metadata))

        # Post-process chunks to ensure minimum size and quality
        return self._post_process_chunks(chunks)

    async def _sliding_window_chunking(self, text: str) -> list[str]:
        """Simple sliding window chunking."""
        chunks_with_metadata = await self._sliding_window_chunking_with_metadata(text)
        return [chunk for chunk, _ in chunks_with_metadata]

    async def _sliding_window_chunking_with_metadata(
        self, text: str
    ) -> list[tuple[str, ChunkMetadata]]:
        """Simple sliding window chunking with metadata."""

        chunks = []
        text_length = len(text)
        start = 0
        chunk_index = 0

        while start < text_length:
            end = start + self.chunk_size

            # Find a good breaking point (end of sentence)
            if end < text_length:
                end = self._find_sentence_boundary(text, start, end)

            chunk_text = text[start:end].strip()
            if chunk_text and len(chunk_text) >= self.min_chunk_size:
                chunk_metadata = self._create_chunk_metadata(
                    chunk_text, chunk_index, start, end
                )
                chunks.append((chunk_text, chunk_metadata))
                chunk_index += 1

            # Move start position with overlap
            overlap_start = max(start + self.chunk_size - self.chunk_overlap, end)
            start = overlap_start if overlap_start > start else end

        return chunks

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""

        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove special characters that might interfere
        text = re.sub(r"[^\w\s\.\!\?\,\;\:\-\(\)\[\]\{\}\"\'\/]", "", text)

        # Normalize line breaks
        text = re.sub(r"\n\s*\n", "\n\n", text)

        return text.strip()

    def _identify_sections(self, text: str) -> list[dict]:
        """Identify logical sections in the text."""

        sections = []
        paragraphs = text.split("\n\n")
        current_pos = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                current_pos += 2  # Account for double newline
                continue

            section_info = {
                "text": paragraph,
                "start": current_pos,
                "end": current_pos + len(paragraph),
                "type": self._classify_section_type(paragraph),
            }
            sections.append(section_info)
            current_pos += len(paragraph) + 2  # Add paragraph + double newline

        return sections

    def _classify_section_type(self, text: str) -> str:
        """Classify the type of text section."""

        text_lines = text.split("\n")
        first_line = text_lines[0].strip()

        # Check for titles/headings
        if self.title_pattern.match(first_line):
            return "title"

        # Check for lists
        if any(self.list_pattern.match(line) for line in text_lines):
            return "list"

        # Check for code blocks
        if "```" in text or text.startswith("    ") or text.startswith("\t"):
            return "code"

        # Default to paragraph
        return "paragraph"

    def _find_sentence_boundary(self, text: str, start: int, target_end: int) -> int:
        """Find the best sentence boundary near the target end position."""

        search_start = max(start + self.chunk_size // 2, target_end - 200)
        search_end = min(len(text), target_end + 100)

        # Look for sentence endings
        best_end = target_end
        for i in range(search_start, search_end):
            if i < len(text) and text[i] in ".!?":
                # Check if this looks like a real sentence ending
                if i + 1 < len(text) and (
                    text[i + 1].isspace() or text[i + 1].isupper()
                ):
                    if abs(i - target_end) < abs(best_end - target_end):
                        best_end = i + 1

        return best_end

    def _get_semantic_overlap(self, current_chunk: str, next_section: str) -> str:
        """Get semantically meaningful overlap between chunks."""

        if len(current_chunk) <= self.chunk_overlap:
            return current_chunk

        # Try to find the last complete sentence within overlap range
        overlap_start = len(current_chunk) - self.chunk_overlap
        overlap_text = current_chunk[overlap_start:]

        # Find the start of the last complete sentence
        sentences = self.sentence_pattern.split(overlap_text)
        if len(sentences) > 1:
            # Return the last complete sentence(s)
            return self.sentence_pattern.split(current_chunk)[-1].strip()

        # Fallback to character-based overlap
        return overlap_text.strip()

    def _create_chunk_metadata(
        self, chunk_text: str, index: int, start: int, end: int
    ) -> ChunkMetadata:
        """Create metadata for a text chunk."""

        # Count sentences
        sentences = self.sentence_pattern.split(chunk_text)
        sentence_count = len([s for s in sentences if s.strip()])

        # Check for titles
        has_title = bool(self.title_pattern.search(chunk_text))

        # Determine content type
        content_type = self._classify_section_type(chunk_text)

        # Calculate quality score
        quality_score = self._calculate_chunk_quality(
            chunk_text, sentence_count, has_title
        )

        return ChunkMetadata(
            chunk_index=index,
            start_char=start,
            end_char=end,
            token_count=self.estimate_tokens(chunk_text),
            sentence_count=sentence_count,
            has_title=has_title,
            quality_score=quality_score,
            content_type=content_type,
        )

    def _calculate_chunk_quality(
        self, text: str, sentence_count: int, has_title: bool
    ) -> float:
        """Calculate a quality score for a chunk (0.0 to 1.0)."""

        score = 0.5  # Base score

        # Length considerations
        length = len(text)
        if self.min_chunk_size <= length <= self.chunk_size:
            score += 0.2
        elif length > self.chunk_size * 1.2:
            score -= 0.1

        # Sentence structure
        if sentence_count >= 2:
            score += 0.2
        elif sentence_count == 0:
            score -= 0.2

        # Content structure
        if has_title:
            score += 0.1

        # Check for completeness (ends with sentence)
        if text.strip().endswith((".", "!", "?")):
            score += 0.1

        # Penalize very repetitive content
        words = text.lower().split()
        if len(set(words)) < len(words) * 0.3:  # Less than 30% unique words
            score -= 0.2

        return max(0.0, min(1.0, score))

    def _post_process_chunks(
        self, chunks: list[tuple[str, ChunkMetadata]]
    ) -> list[tuple[str, ChunkMetadata]]:
        """Post-process chunks to improve quality."""

        if not chunks:
            return chunks

        processed_chunks = []

        for i, (chunk_text, metadata) in enumerate(chunks):
            # Skip chunks that are too small unless they're the last one
            if len(chunk_text) < self.min_chunk_size and i < len(chunks) - 1:
                # Merge with next chunk if possible
                if i + 1 < len(chunks):
                    next_chunk, next_metadata = chunks[i + 1]
                    merged_text = chunk_text + "\n\n" + next_chunk
                    if len(merged_text) <= self.chunk_size * 1.2:
                        # Update the next chunk and skip current
                        chunks[i + 1] = (
                            merged_text,
                            self._create_chunk_metadata(
                                merged_text,
                                metadata.chunk_index,
                                metadata.start_char,
                                next_metadata.end_char,
                            ),
                        )
                        continue

            processed_chunks.append((chunk_text, metadata))

        return processed_chunks

    def _get_text_overlap(self, text: str) -> str:
        """Get overlap text from the end of a chunk."""

        if len(text) <= self.chunk_overlap:
            return text

        # Get the last chunk_overlap characters
        overlap_text = text[-self.chunk_overlap :]

        # Try to start at a sentence boundary
        for i in range(len(overlap_text)):
            if overlap_text[i] in ".!?":
                return overlap_text[i + 1 :].strip()

        # If no sentence boundary, return the overlap as is
        return overlap_text.strip()

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count with improved accuracy."""
        if not text:
            return 0

        # More sophisticated token estimation
        # Account for whitespace, punctuation, and word boundaries
        words = len(text.split())
        chars = len(text)

        # Empirical formula that's more accurate than simple division
        # Based on OpenAI's tokenization patterns
        estimated_tokens = int(words * 1.3 + chars * 0.25)

        # Ensure minimum of word count (each word is at least 1 token)
        return max(words, estimated_tokens)

    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to approximately max_tokens with smart boundaries."""
        if not text:
            return text

        # More accurate character estimation
        estimated_chars = max_tokens * 3.5  # More conservative estimate

        if len(text) <= estimated_chars:
            return text

        # First truncate to approximate length
        truncated = text[: int(estimated_chars)]

        # Fine-tune by checking actual token estimate
        while self.estimate_tokens(truncated) > max_tokens and len(truncated) > 100:
            # Find the last sentence boundary within safe range
            search_start = max(0, len(truncated) - 200)
            boundary_found = False

            for i in range(len(truncated) - 1, search_start, -1):
                if truncated[i] in ".!?":
                    truncated = truncated[: i + 1]
                    boundary_found = True
                    break

            if not boundary_found:
                # No sentence boundary found, truncate by words
                words = truncated.split()
                truncated = " ".join(words[:-1])

            if len(truncated) <= 100:  # Prevent over-truncation
                break

        return truncated

    def get_chunk_statistics(self, chunks: list[str]) -> dict:
        """Get statistics about the chunks."""
        if not chunks:
            return {}

        chunk_lengths = [len(chunk) for chunk in chunks]
        token_counts = [self.estimate_tokens(chunk) for chunk in chunks]

        return {
            "total_chunks": len(chunks),
            "avg_chunk_length": sum(chunk_lengths) / len(chunk_lengths),
            "min_chunk_length": min(chunk_lengths),
            "max_chunk_length": max(chunk_lengths),
            "avg_token_count": sum(token_counts) / len(token_counts),
            "total_tokens": sum(token_counts),
            "total_characters": sum(chunk_lengths),
        }
