import sys
import json
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict
from docling.document_converter import DocumentConverter
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Splits text into overlapping chunks for semantic search.
    Uses character-based chunking with overlap to preserve context.
    """
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]

        # Try to break at sentence boundary if possible
        if end < text_len:
            last_period = chunk.rfind(".")
            last_newline = chunk.rfind("\n")
            break_point = max(last_period, last_newline)
            # Only break if we're past 70% of chunk
            if break_point > chunk_size * 0.7:
                chunk = chunk[: break_point + 1]
                end = start + break_point + 1

        if chunk.strip():
            chunks.append(chunk.strip())

        start = end - overlap

    return chunks


def _semantic_search(
    chunks: List[str], keywords: List[str], model: SentenceTransformer, top_k: int = 3
) -> Dict[str, List[str]]:
    """
    Performs semantic similarity search to find most relevant chunks per keyword.
    Returns top-k chunks for each keyword based on cosine similarity.
    """
    if not chunks or not keywords:
        return {}

    # Encode all chunks once
    chunk_embeddings = model.encode(chunks, convert_to_tensor=False)

    results = {}
    for keyword in keywords:
        # Encode the keyword query
        keyword_embedding = model.encode([keyword], convert_to_tensor=False)

        # Calculate cosine similarity
        similarities = cosine_similarity(keyword_embedding, chunk_embeddings)[0]

        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        # Filter out low-similarity results (threshold: 0.2)
        relevant_chunks = []
        for idx in top_indices:
            if similarities[idx] > 0.2:
                relevant_chunks.append(chunks[idx])

        if relevant_chunks:
            results[keyword] = relevant_chunks

    return results


def process_pdf(pdf_path: str, targets: Optional[List[str]] = None):
    """
    Ingests and processes a PDF file using the docling package.
    Implements semantic RAG-lite with sentence-transformers for
    keyword-targeted extraction.
    """
    if not Path(pdf_path).exists():
        error_res = {"error": f"PDF file not found at {pdf_path}"}
        print(json.dumps(error_res))
        sys.exit(1)

    try:
        # Convert PDF to markdown
        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        content = result.document.export_to_markdown()

        # Semantic chunking with overlap
        chunks = _chunk_text(content, chunk_size=500, overlap=50)

        if not chunks:
            error_res = {"error": "No content extracted from PDF"}
            print(json.dumps(error_res))
            sys.exit(1)

        relevant_chunks: List[str] = []
        search_metadata = {}

        if targets and len(targets) > 0:
            # Load sentence-transformer model (lightweight, fast)
            model = SentenceTransformer("all-MiniLM-L6-v2")

            # Perform semantic search for each target keyword
            search_results = _semantic_search(chunks, targets, model, top_k=3)

            # Flatten results while preserving keyword context
            for _keyword, keyword_chunks in search_results.items():
                for chunk in keyword_chunks:
                    if chunk not in relevant_chunks:  # Dedup
                        relevant_chunks.append(chunk)

            search_metadata = {
                "search_method": "semantic_similarity",
                "keywords_matched": list(search_results.keys()),
                "chunks_per_keyword": {k: len(v) for k, v in search_results.items()},
            }
        else:
            # No targets: return first 5 chunks as overview
            relevant_chunks = chunks[:5]
            search_metadata = {"search_method": "default_overview"}

        evidence = {
            "status": "success",
            "file": pdf_path,
            "query_results": relevant_chunks,
            "metadata": {
                "total_chunks": len(chunks),
                "relevant_chunks_found": len(relevant_chunks),
                "targets_queried": targets,
                **search_metadata,
            },
        }

        # STRICT RULE: Print exactly one JSON string to stdout
        print(json.dumps(evidence))
        sys.exit(0)
    except Exception as e:
        error_res = {"error": str(e)}
        print(json.dumps(error_res))
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage = "Usage: python run_doc_analyst.py <pdf> [<targets>]"
        print(json.dumps({"error": usage}))
        sys.exit(1)

    path = sys.argv[1]
    query_targets = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    process_pdf(path, query_targets)
