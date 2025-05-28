"""URL content extraction service for web scraping."""

import asyncio
import re
from typing import Optional
from urllib.parse import urlparse

import aiohttp
import trafilatura
from trafilatura.settings import use_config

from ..core.exceptions import DocumentIngestionError


class URLExtractor:
    """Service for extracting content from web URLs."""

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = None

        # Configure trafilatura for better extraction
        self.config = use_config()
        self.config.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")
        self.config.set("DEFAULT", "MIN_EXTRACTED_SIZE", "100")

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 Safari/537.36"
                )
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def extract_content(self, url: str) -> str:
        """Extract text content from a URL with retry logic."""

        if not self.session:
            raise DocumentIngestionError(
                "URLExtractor must be used as async context manager"
            )

        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise DocumentIngestionError(f"Invalid URL format: {url}")

        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return await self._extract_content_attempt(url)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    # Wait before retry with exponential backoff
                    await asyncio.sleep(2**attempt)
                    continue
                break

        raise DocumentIngestionError(
            f"Failed to extract content from {url} after {self.max_retries} attempts. "
            f"Last error: {str(last_exception)}"
        )

    async def _extract_content_attempt(self, url: str) -> str:
        """Single attempt to extract content from URL."""

        try:
            # Download the webpage
            async with self.session.get(url) as response:
                if response.status == 404:
                    raise DocumentIngestionError(f"URL not found: {url}")
                elif response.status == 403:
                    raise DocumentIngestionError(f"Access forbidden: {url}")
                elif response.status >= 400:
                    raise DocumentIngestionError(
                        f"HTTP error {response.status} when accessing {url}"
                    )

                # Check content type
                content_type = response.headers.get("content-type", "").lower()

                if "pdf" in content_type:
                    raise DocumentIngestionError(
                        f"URL points to PDF content. Use PDF extraction instead: {url}"
                    )

                if not any(
                    ct in content_type for ct in ["text/html", "application/xhtml"]
                ):
                    raise DocumentIngestionError(
                        f"Unsupported content type {content_type} for URL: {url}"
                    )

                html_content = await response.text()

            # Extract main content using trafilatura
            extracted_text = trafilatura.extract(
                html_content,
                config=self.config,
                include_comments=False,
                include_tables=True,
                include_links=False,
                include_images=False,
                favor_precision=True,
                favor_recall=False,
                deduplicate=True,
                url=url,
            )

            if not extracted_text:
                # Fallback: try with different settings
                extracted_text = trafilatura.extract(
                    html_content,
                    include_comments=False,
                    include_tables=True,
                    favor_precision=False,
                    favor_recall=True,
                    url=url,
                )

            if not extracted_text:
                raise DocumentIngestionError(
                    f"No extractable content found at URL: {url}"
                )

            # Clean and format the extracted text
            cleaned_text = self._clean_extracted_content(extracted_text, url)

            if len(cleaned_text.strip()) < 100:
                raise DocumentIngestionError(
                    f"Extracted content too short (less than 100 characters) from URL: {url}"
                )

            return cleaned_text

        except aiohttp.ClientError as e:
            raise DocumentIngestionError(f"Network error accessing {url}: {str(e)}")
        except asyncio.TimeoutError:
            raise DocumentIngestionError(f"Timeout while accessing {url}")

    def _clean_extracted_content(self, text: str, url: str) -> str:
        """Clean and format extracted web content."""

        if not text:
            return ""

        # Add URL as metadata at the beginning
        url_info = f"Source: {url}\n\n"

        # Split into paragraphs and clean
        paragraphs = text.split("\n\n")
        cleaned_paragraphs = []

        for paragraph in paragraphs:
            cleaned_para = self._clean_paragraph(paragraph)
            if cleaned_para:
                cleaned_paragraphs.append(cleaned_para)

        # Join paragraphs
        result = "\n\n".join(cleaned_paragraphs)

        # Final cleaning
        result = self._final_text_cleanup(result)

        return url_info + result

    def _clean_paragraph(self, paragraph: str) -> str:
        """Clean a single paragraph."""

        if not paragraph:
            return ""

        # Split into sentences
        sentences = re.split(r"[.!?]+", paragraph)
        cleaned_sentences = []

        for sentence in sentences:
            # Clean whitespace and basic formatting
            cleaned_sentence = " ".join(sentence.split())

            # Skip if too short or likely artifact
            if len(cleaned_sentence) < 10:
                continue

            if self._is_navigation_or_ui_text(cleaned_sentence):
                continue

            # Remove common web prefixes/suffixes
            cleaned_sentence = self._remove_web_artifacts(cleaned_sentence)

            if cleaned_sentence:
                cleaned_sentences.append(cleaned_sentence)

        if not cleaned_sentences:
            return ""

        # Rejoin sentences
        result = ". ".join(cleaned_sentences)

        # Add final period if missing
        if result and not result.endswith((".", "!", "?")):
            result += "."

        return result

    def _is_navigation_or_ui_text(self, text: str) -> bool:
        """Check if text is likely navigation or UI element."""

        text_lower = text.lower().strip()

        # Common navigation and UI patterns
        ui_patterns = [
            r"^(click|tap|press)\s+(here|this|button)",
            r"^(home|about|contact|menu|search|login|register)",
            r"^(previous|next|back|forward|continue)",
            r"^(skip to|jump to|go to)",
            r"^(share|like|follow|subscribe)",
            r"^(cookie|privacy|terms|policy)",
            r"^\d+\s+(comments?|replies?|likes?)",
            r"^(loading|please wait|redirecting)",
            r"^(error|warning|success|info):",
            r"^\w+\s+\|\s+\w+",  # Breadcrumb pattern
        ]

        for pattern in ui_patterns:
            if re.match(pattern, text_lower):
                return True

        # Check for very short navigation-like text
        if len(text) < 30 and any(
            word in text_lower
            for word in ["menu", "nav", "link", "button", "tab", "page", "section"]
        ):
            return True

        return False

    def _remove_web_artifacts(self, text: str) -> str:
        """Remove common web artifacts from text."""

        # Remove email addresses
        text = re.sub(r"\S+@\S+\.\S+", "", text)

        # Remove URLs (except if they're part of meaningful content)
        text = re.sub(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            "",
            text,
        )

        # Remove phone numbers
        text = re.sub(r"[\+]?[1-9]?[0-9]{3}-?[0-9]{3}-?[0-9]{4}", "", text)

        # Remove excessive punctuation
        text = re.sub(r"[.]{3,}", "...", text)
        text = re.sub(r"[-]{3,}", "---", text)

        # Remove standalone symbols
        text = re.sub(r"\s+[|•→←↑↓]\s+", " ", text)

        # Clean up whitespace
        text = " ".join(text.split())

        return text.strip()

    def _final_text_cleanup(self, text: str) -> str:
        """Final cleanup of the entire text."""

        # Remove excessive newlines
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove lines that are just whitespace or punctuation
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line and not re.match(r"^[^\w]*$", line):
                cleaned_lines.append(line)

        result = "\n".join(cleaned_lines)

        # Final whitespace cleanup
        result = result.strip()

        return result

    async def extract_metadata(self, url: str) -> dict[str, Optional[str]]:
        """Extract metadata from URL (title, description, etc.)."""

        if not self.session:
            raise DocumentIngestionError(
                "URLExtractor must be used as async context manager"
            )

        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return {}

                html_content = await response.text()

            # Extract metadata using trafilatura
            metadata = trafilatura.extract_metadata(html_content)

            result = {}
            if metadata:
                result["title"] = getattr(metadata, "title", None)
                result["author"] = getattr(metadata, "author", None)
                result["description"] = getattr(metadata, "description", None)
                result["sitename"] = getattr(metadata, "sitename", None)
                result["date"] = getattr(metadata, "date", None)
                result["url"] = url

            return result

        except Exception:
            # If metadata extraction fails, return empty dict
            return {"url": url}

    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and accessible for content extraction."""

        try:
            parsed = urlparse(url)

            # Check basic URL structure
            if not parsed.scheme or not parsed.netloc:
                return False

            # Check if scheme is supported
            if parsed.scheme not in ["http", "https"]:
                return False

            # Check for common file extensions that we can't process
            path = parsed.path.lower()
            unsupported_extensions = [
                ".pdf",
                ".doc",
                ".docx",
                ".xls",
                ".xlsx",
                ".ppt",
                ".pptx",
                ".zip",
                ".rar",
                ".tar",
                ".gz",
                ".mp3",
                ".mp4",
                ".avi",
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".svg",
                ".exe",
                ".dmg",
            ]

            for ext in unsupported_extensions:
                if path.endswith(ext):
                    return False

            return True

        except Exception:
            return False
