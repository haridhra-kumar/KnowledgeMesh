import re
import uuid
from typing import List, Dict, Any

def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences while protecting abbreviations and handling PDF line-breaks."""
    if not text:
        return []
    # Rejoin words split across line breaks
    cleaned = re.sub(r'(\b[a-zA-Z]{2,})[-–—]\s*\n\s*([a-zA-Z]{2,}\b)', r'\1\2', text)
    # Paragraphs are separated by 2 or more newlines
    paragraphs = re.split(r'\n\s*\n+', cleaned)

    sentences: List[str] = []
    for para in paragraphs:
        # Convert single newlines inside a paragraph to spaces
        para_clean = re.sub(r'\s*\n\s*', ' ', para).strip()
        if not para_clean:
            continue
        # Protect common abbreviations
        masked = re.sub(r'\b(Rs|INR|Mr|Mrs|Ms|Dr|Ltd|Inc|Corp|No|Vol|FY|vs|eg|ie|approx|bn|mn|cr)\.', r'\1__DOT__', para_clean, flags=re.IGNORECASE)
        # Split on sentence boundaries
        raw_sents = re.split(r'(?<=[.?!])\s+', masked)
        for s in raw_sents:
            unmasked = s.replace('__DOT__', '.').strip()
            if unmasked:
                sentences.append(unmasked)

    return sentences

def create_chunks(
    pages: List[Dict[str, Any]],
    chunk_size_words: int = 1000,
    overlap_words: int = 150
) -> List[Dict[str, Any]]:
    """
    Chunk page text while preserving page numbers and source metadata.
    If a page has substantial text, it can be split into chunks.
    If pages are short, they can be grouped, but each chunk explicitly tracks its page(s).
    """
    chunks: List[Dict[str, Any]] = []

    for page_data in pages:
        page_num = page_data["page_number"]
        text = page_data["text"].strip()

        if not text:
            continue

        words = text.split()
        if len(words) <= chunk_size_words:
            # Entire page fits in one chunk
            chunks.append({
                "chunk_id": f"chunk_p{page_num}_{uuid.uuid4().hex[:8]}",
                "page_number": page_num,
                "start_page": page_num,
                "end_page": page_num,
                "text": text,
                "word_count": len(words)
            })
        else:
            # Split page into overlapping chunks
            sentences = split_into_sentences(text)
            current_chunk_sentences: List[str] = []
            current_word_count = 0
            sub_idx = 1

            for sentence in sentences:
                sent_words = len(sentence.split())
                if current_word_count + sent_words > chunk_size_words and current_chunk_sentences:
                    chunk_text = " ".join(current_chunk_sentences)
                    chunks.append({
                        "chunk_id": f"chunk_p{page_num}_{sub_idx}_{uuid.uuid4().hex[:8]}",
                        "page_number": page_num,
                        "start_page": page_num,
                        "end_page": page_num,
                        "text": chunk_text,
                        "word_count": len(chunk_text.split())
                    })
                    sub_idx += 1

                    # Keep last sentence(s) for overlap
                    overlap_sentences: List[str] = []
                    overlap_count = 0
                    for s in reversed(current_chunk_sentences):
                        sw = len(s.split())
                        if overlap_count + sw <= overlap_words:
                            overlap_sentences.insert(0, s)
                            overlap_count += sw
                        else:
                            break
                    current_chunk_sentences = overlap_sentences + [sentence]
                    current_word_count = sum(len(s.split()) for s in current_chunk_sentences)
                else:
                    current_chunk_sentences.append(sentence)
                    current_word_count += sent_words

            if current_chunk_sentences:
                chunk_text = " ".join(current_chunk_sentences)
                chunks.append({
                    "chunk_id": f"chunk_p{page_num}_{sub_idx}_{uuid.uuid4().hex[:8]}",
                    "page_number": page_num,
                    "start_page": page_num,
                    "end_page": page_num,
                    "text": chunk_text,
                    "word_count": len(chunk_text.split())
                })

    return chunks
