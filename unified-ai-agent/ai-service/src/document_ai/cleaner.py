"""Text cleaning and normalization utility for Document AI and OCR outputs."""
import re


class DocumentTextCleaner:
    """Normalizes extracted and OCR text while strictly preserving numbers, dates, currency, and IDs."""

    @staticmethod
    def clean(text: str) -> str:
        """Clean raw OCR/extracted document text."""
        if not text:
            return ""

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove null bytes and non-printable control characters (except newline, tab)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

        # Fix OCR broken hyphenations at line ends (e.g. "certifi-\ncate" -> "certificate")
        text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)

        # Remove standalone OCR noise characters (like stray tildes, backticks)
        text = re.sub(r"(?<=\s)[~`^|_](?=\s)", "", text)

        # Normalize multiple horizontal whitespaces to a single space
        lines = []
        for line in text.split("\n"):
            cleaned_line = re.sub(r"[ \t]+", " ", line).strip()
            lines.append(cleaned_line)

        # Remove excessive blank lines (more than 2 consecutive)
        cleaned = "\n".join(lines)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        return cleaned.strip()
