"""Text cleaning module for government scheme documents.

Preserves:
- Paragraph boundaries
- Section titles and headings
- Monetary figures (e.g. ₹, Rs., INR), percentages, dates, and age brackets
- Bullet points and lists
- Government scheme acronyms and official terminology
"""
import re


class TextCleaner:
    """Cleans extracted document text without destroying vital domain information."""

    # Matches non-breaking spaces and special space characters
    UNICODE_SPACES = re.compile(r"[\u00A0\u1680\u180E\u2000-\u200B\u202F\u205F\u3000\uFEFF]")
    # Matches consecutive horizontal spaces (spaces and tabs)
    HORIZONTAL_SPACES = re.compile(r"[ \t]+")
    # Matches more than 2 consecutive newlines
    EXCESSIVE_NEWLINES = re.compile(r"\n{3,}")
    # Matches line hyphenation at word breaks (e.g. "govern-\nment" -> "government")
    HYPHENATED_LINEBREAK = re.compile(r"(\w+)-\n(\w+)")

    @classmethod
    def clean(cls, text: str) -> str:
        """Clean and normalize extracted text while preserving semantic structure."""
        if not text:
            return ""

        # Step 1: Replace non-standard Unicode whitespace with standard space
        text = cls.UNICODE_SPACES.sub(" ", text)

        # Step 2: Fix hyphenated words broken across line breaks (common in PDF columns)
        text = cls.HYPHENATED_LINEBREAK.sub(r"\1\2", text)

        # Step 3: Normalize carriage returns to standard newlines
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Step 4: Clean lines individually
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            # Strip trailing/leading spaces of each line, collapse inner spaces
            cleaned_line = cls.HORIZONTAL_SPACES.sub(" ", line).strip()
            cleaned_lines.append(cleaned_line)

        # Recombine lines
        normalized_text = "\n".join(cleaned_lines)

        # Step 5: Collapse 3+ newlines to standard double newline (paragraph boundary)
        normalized_text = cls.EXCESSIVE_NEWLINES.sub("\n\n", normalized_text)

        # Step 6: Trim overall string
        return normalized_text.strip()
