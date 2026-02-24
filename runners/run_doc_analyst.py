import sys
import json
from pathlib import Path


# Placeholder for the actual docling ingestion logic
# In reality, this script is executed by `envs/docling/bin/python`
def process_pdf(pdf_path: str):
    """
    Ingests and processes a PDF file using the docling package.
    Outputs structured analysis to stdout as JSON.
    """
    if not Path(pdf_path).exists():
        error_res = {"error": f"PDF file not found at {pdf_path}"}
        print(json.dumps(error_res))
        sys.exit(1)

    try:
        # NOTE: This is where DocumentConverter would occur,
        # running strictly in the ml-heavy env.

        # Simulated Output for now:
        evidence = {
            "status": "success",
            "file": pdf_path,
            "text": "Extracted text content...",
        }

        # STRICT RULE: Print exactly one JSON string to stdout
        print(json.dumps(evidence))
        sys.exit(0)
    except Exception as e:
        error_res = {"error": str(e)}
        print(json.dumps(error_res))
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        error_msg = {"error": "Usage: python run_doc_analyst.py <pdf_path>"}
        print(json.dumps(error_msg))
        sys.exit(1)

    pdf_path = sys.argv[1]
    process_pdf(pdf_path)
