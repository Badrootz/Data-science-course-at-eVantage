import re

def chunk_document(text: str, source_page: str, chunk_size: int = 500, overlap: int = 100) -> list[dict]:
    """
    Splits text using a sliding window approach based on word token counts.
    
    Args:
        text: Full document string.
        source_page: Source page filename or identifier.
        chunk_size: Target number of tokens per chunk (len(text.split())).
        overlap: Token overlap between consecutive chunks.
        
    Returns:
        List of dicts containing chunk metadata and text.
    """
    # Find all non-whitespace tokens with their character positions
    matches = list(re.finditer(r'\S+', text))
    if not matches:
        return []

    chunks = []
    step = chunk_size - overlap
    if step <= 0:
        step = max(1, chunk_size // 2)

    total_tokens = len(matches)
    chunk_index = 1
    start_token_idx = 0

    while start_token_idx < total_tokens:
        end_token_idx = min(start_token_idx + chunk_size, total_tokens)
        
        char_start = matches[start_token_idx].start()
        char_end = matches[end_token_idx - 1].end()
        
        chunk_text = text[char_start:char_end]
        clean_source_name = source_page.replace(".txt", "")
        chunk_id = f"{clean_source_name}_chunk_{chunk_index:03d}"
        
        chunks.append({
            "chunk_id": chunk_id,
            "source_page": source_page,
            "chunk_text": chunk_text,
            "char_start": char_start,
            "token_count": end_token_idx - start_token_idx,
            "char_length": len(chunk_text)
        })

        if end_token_idx == total_tokens:
            break

        start_token_idx += step
        chunk_index += 1

    return chunks


def chunk_all_documents(scraped_pages_dict: dict[str, str], chunk_size: int = 500, overlap: int = 100) -> list[dict]:
    """
    Chunks multiple documents provided as a dictionary of {source_page: text}.
    
    Returns:
        List of all chunk dicts across all documents.
    """
    all_chunks = []
    for source_page, text in scraped_pages_dict.items():
        doc_chunks = chunk_document(text, source_page=source_page, chunk_size=chunk_size, overlap=overlap)
        all_chunks.extend(doc_chunks)
    return all_chunks


if __name__ == "__main__":
    sample_text = "Formula One (also known as Formula 1 or F1) is the highest class of international racing for open-wheel single-seater formula cars."
    res = chunk_document(sample_text, "Formula_One.txt", chunk_size=10, overlap=3)
    print(f"Generated {len(res)} test chunks:")
    for c in res:
        print(c)
