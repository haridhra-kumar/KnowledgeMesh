import pytest
from app.services.chunker import create_chunks

def test_chunking_small_pages():
    pages = [
        {"page_number": 1, "text": "Sentence one. Sentence two. Short page."},
        {"page_number": 2, "text": "Page two content with some more information."}
    ]
    chunks = create_chunks(pages, chunk_size_words=100)
    assert len(chunks) == 2
    assert chunks[0]["page_number"] == 1
    assert chunks[1]["page_number"] == 2

def test_chunking_large_page_splits():
    words = ["word" for _ in range(500)]
    long_text = ". ".join([" ".join(words[i:i+50]) for i in range(0, 500, 50)]) + "."
    pages = [{"page_number": 1, "text": long_text}]
    chunks = create_chunks(pages, chunk_size_words=100, overlap_words=20)
    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk["page_number"] == 1
        assert "chunk_id" in chunk
        assert chunk["word_count"] > 0
