import sys
import json
from pathlib import Path
from typing import Optional
from docling.document_converter import DocumentConverter


def process_pdf(pdf_path: str, targets: Optional[list[str]] = None):
    """
    Ingests and processes a PDF file using the docling package.
    Provides a queryable interface by returning targeted chunks.
    """
    if not Path(pdf_path).exists():
        error_res = {"error": f"PDF file not found at {pdf_path}"}
        print(json.dumps(error_res))
        sys.exit(1)

    try:
        converter = DocumentConverter()
        result = converter.convert(pdf_path)

        # Export to markdown for chunking
        content = result.document.export_to_markdown()

        # RAG-lite: Simple keyword-based chunking
        chunks = content.split("\n\n")
        relevant_chunks = []

        if targets:
            for chunk in chunks:
                if any(t.lower() in chunk.lower() for t in targets):
                    relevant_chunks.append(chunk)
        else:
            # Default to first few chunks if no targets
            relevant_chunks = chunks[:5]

        evidence = {
            "status": "success",
            "file": pdf_path,
            "query_results": relevant_chunks,
            "metadata": {
                "total_chunks": len(chunks),
                "relevant_chunks_found": len(relevant_chunks),
                "targets_queried": targets,
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
