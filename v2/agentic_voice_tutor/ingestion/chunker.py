import config


def chunk_text(text, size=None, overlap=None):
    """Split text into chunks of `size` words, each sharing `overlap` words
    with the previous chunk."""
    size = config.CHUNK_SIZE_WORDS if size is None else size
    overlap = config.CHUNK_OVERLAP_WORDS if overlap is None else overlap
    if size <= 0:
        raise ValueError("chunk size must be positive")
    if not 0 <= overlap < size:
        raise ValueError("overlap must be >= 0 and smaller than the chunk size")
    words = text.split()
    if not words:
        return []
    step = size - overlap
    chunks = []
    for start in range(0, len(words), step):
        chunks.append(" ".join(words[start:start + size]))
        if start + size >= len(words):
            break
    return chunks
