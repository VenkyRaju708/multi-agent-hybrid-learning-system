import io

from pypdf import PdfReader


def parse_pdf(file):
    """Extract text from a PDF given a path, a file-like object or raw bytes."""
    if isinstance(file, (bytes, bytearray)):
        file = io.BytesIO(file)
    reader = PdfReader(file)
    return "\n".join([p.extract_text() or "" for p in reader.pages])


def load_document_bytes(data, filename=""):
    """Text of an uploaded document. Plain .txt is accepted for test sets."""
    if filename.lower().endswith(".txt"):
        return data.decode("utf-8", errors="replace")
    return parse_pdf(data)
