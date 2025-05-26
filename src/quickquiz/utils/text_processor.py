"""Text processing utilities for chunking and preprocessing."""

from typing import List, Optional
import re


class TextProcessor:
    """Service for processing and chunking text content."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    async def chunk_text(self, text: str, preserve_structure: bool = True) -> List[str]:
        """Split text into chunks with optional structure preservation."""
        
        if not text.strip():
            return []
        
        # Clean the text first
        cleaned_text = self._clean_text(text)
        
        if preserve_structure:
            return await self._semantic_chunking(cleaned_text)
        else:
            return await self._sliding_window_chunking(cleaned_text)
    
    async def _semantic_chunking(self, text: str) -> List[str]:
        """Chunk text while preserving semantic structure."""
        
        chunks = []
        
        # Split by major sections (double newlines)
        sections = text.split('\n\n')
        
        current_chunk = ""
        current_size = 0
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            section_size = len(section)
            
            # If adding this section would exceed chunk size
            if current_size + section_size > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append(current_chunk.strip())
                
                # Start new chunk with overlap
                if self.chunk_overlap > 0:
                    overlap_text = self._get_text_overlap(current_chunk)
                    current_chunk = overlap_text + "\n\n" + section
                    current_size = len(current_chunk)
                else:
                    current_chunk = section
                    current_size = section_size
            else:
                # Add section to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + section
                else:
                    current_chunk = section
                current_size = len(current_chunk)
        
        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def _sliding_window_chunking(self, text: str) -> List[str]:
        """Simple sliding window chunking."""
        
        chunks = []
        text_length = len(text)
        start = 0
        
        while start < text_length:
            end = start + self.chunk_size
            
            # Find a good breaking point (end of sentence)
            if end < text_length:
                # Look for sentence endings near the target end
                for i in range(end, max(start + self.chunk_size // 2, end - 100), -1):
                    if text[i] in '.!?':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            if start <= 0:
                start = end
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might interfere
        text = re.sub(r'[^\w\s\.\!\?\,\;\:\-\(\)\[\]\{\}\"\'\/]', '', text)
        
        # Normalize line breaks
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    def _get_text_overlap(self, text: str) -> str:
        """Get overlap text from the end of a chunk."""
        
        if len(text) <= self.chunk_overlap:
            return text
        
        # Get the last chunk_overlap characters
        overlap_text = text[-self.chunk_overlap:]
        
        # Try to start at a sentence boundary
        for i in range(len(overlap_text)):
            if overlap_text[i] in '.!?':
                return overlap_text[i+1:].strip()
        
        # If no sentence boundary, return the overlap as is
        return overlap_text.strip()
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Rough approximation: 1 token ≈ 4 characters for English
        return len(text) // 4
    
    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to approximately max_tokens."""
        max_chars = max_tokens * 4  # Rough approximation
        
        if len(text) <= max_chars:
            return text
        
        # Truncate and try to end at a sentence boundary
        truncated = text[:max_chars]
        
        # Find the last sentence ending
        for i in range(len(truncated) - 1, max(0, len(truncated) - 100), -1):
            if truncated[i] in '.!?':
                return truncated[:i+1]
        
        return truncated
