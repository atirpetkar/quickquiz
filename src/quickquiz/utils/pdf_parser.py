"""PDF parsing utilities."""

import os
import tempfile

import aiohttp
import pdfplumber
import trafilatura

from ..core.exceptions import DocumentIngestionError


class PDFParser:
    """Service for parsing PDF documents and web content."""

    async def extract_from_url(self, url: str) -> str:
        """Extract text from a PDF URL."""

        try:
            # Download PDF from URL
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise DocumentIngestionError(
                            f"Failed to download PDF: HTTP {response.status}"
                        )

                    pdf_content = await response.read()

            return await self.extract_from_bytes(pdf_content)

        except aiohttp.ClientError as e:
            raise DocumentIngestionError(f"Failed to download PDF: {str(e)}")
        except Exception as e:
            raise DocumentIngestionError(
                f"Failed to extract text from PDF URL: {str(e)}"
            )

    async def extract_from_web_url(self, url: str) -> str:
        """Extract text content from a web URL using trafilatura."""

        try:
            # Download the webpage
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise DocumentIngestionError(
                            f"Failed to download webpage: HTTP {response.status}"
                        )

                    html_content = await response.text()

            # Extract main content using trafilatura
            extracted_text = trafilatura.extract(
                html_content,
                include_comments=False,
                include_tables=True,
                include_links=False,
                favor_precision=True,
                deduplicate=True,
            )

            if not extracted_text:
                raise DocumentIngestionError("No text content extracted from webpage")

            # Clean and format the extracted text
            cleaned_text = self._clean_web_content(extracted_text)

            return cleaned_text

        except aiohttp.ClientError as e:
            raise DocumentIngestionError(f"Failed to download webpage: {str(e)}")
        except Exception as e:
            raise DocumentIngestionError(
                f"Failed to extract text from web URL: {str(e)}"
            )

    def _clean_web_content(self, text: str) -> str:
        """Clean and format extracted web content."""

        if not text:
            return ""

        # Split into lines and clean each one
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            # Remove excessive whitespace
            cleaned_line = " ".join(line.split())

            # Skip very short lines and common web artifacts
            if len(cleaned_line) > 3 and not self._is_web_artifact(cleaned_line):
                cleaned_lines.append(cleaned_line)

        # Join lines with appropriate spacing
        result = "\n".join(cleaned_lines)

        # Remove excessive newlines
        while "\n\n\n" in result:
            result = result.replace("\n\n\n", "\n\n")

        return result.strip()

    def _is_web_artifact(self, line: str) -> bool:
        """Check if a line is likely a web artifact to be filtered out."""

        line_lower = line.lower().strip()

        # Common web artifacts to filter
        artifacts = [
            "click here",
            "read more",
            "learn more",
            "sign up",
            "log in",
            "subscribe",
            "cookie",
            "privacy policy",
            "terms of service",
            "advertisement",
            "sponsored",
        ]

        # Check if line is too short or contains common artifacts
        if len(line) < 10:
            return True

        for artifact in artifacts:
            if artifact in line_lower:
                return True

        return False

    async def extract_from_bytes(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF bytes."""

        try:
            # Create a temporary file to work with pdfplumber
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                tmp_file.write(pdf_bytes)
                tmp_file.flush()

                text = await self._extract_text_from_file(tmp_file.name)

                # Clean up temporary file
                os.unlink(tmp_file.name)

                return text

        except Exception as e:
            raise DocumentIngestionError(
                f"Failed to extract text from PDF bytes: {str(e)}"
            )

    async def extract_from_file(self, file_path: str) -> str:
        """Extract text from a PDF file path."""

        try:
            return await self._extract_text_from_file(file_path)
        except Exception as e:
            raise DocumentIngestionError(
                f"Failed to extract text from PDF file: {str(e)}"
            )

    async def _extract_text_from_file(self, file_path: str) -> str:
        """Extract text from PDF file using pdfplumber."""

        text_content = []

        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                try:
                    # Extract text from page
                    page_text = page.extract_text()

                    if page_text:
                        # Clean and format the text
                        cleaned_text = self._clean_page_text(page_text)
                        if cleaned_text.strip():
                            text_content.append(
                                f"<!-- Page {page_num + 1} -->\n{cleaned_text}"
                            )

                except Exception as e:
                    # Log warning but continue with other pages
                    print(
                        f"Warning: Failed to extract text from page {page_num + 1}: {str(e)}"
                    )
                    continue

        if not text_content:
            raise DocumentIngestionError("No text content extracted from PDF")

        return "\n\n".join(text_content)

    def _clean_page_text(self, text: str) -> str:
        """Clean and format extracted text."""

        if not text:
            return ""

        # Basic text cleaning
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            # Remove excessive whitespace
            cleaned_line = " ".join(line.split())

            # Skip very short lines (likely artifacts)
            if len(cleaned_line) > 3:
                cleaned_lines.append(cleaned_line)

        # Join lines with appropriate spacing
        result = "\n".join(cleaned_lines)

        # Remove excessive newlines
        while "\n\n\n" in result:
            result = result.replace("\n\n\n", "\n\n")

        return result.strip()
