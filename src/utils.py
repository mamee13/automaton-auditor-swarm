import json
import os
import tempfile
import httpx
from typing import Dict, Any


def load_rubric(file_path: str = "rubric/week2_rubric.json") -> Dict[str, Any]:
    """
    Loads the machine-readable rubric from a JSON file.
    """
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Rubric file not found at {file_path}")
    except json.JSONDecodeError as e:
        msg = f"Error decoding rubric JSON: {str(e)}"
        raise ValueError(msg)


def get_dimension_by_id(
    rubric: Dict[str, Any],
    dimension_id: str,
) -> Dict[str, Any]:
    """
    Retrieves a specific dimension from the loaded rubric.
    """
    for dimension in rubric.get("dimensions", []):
        if dimension.get("id") == dimension_id:
            return dimension
    raise ValueError(f"Dimension ID '{dimension_id}' not found in rubric")


def download_remote_pdf(url: str) -> str:
    """
    Downloads a PDF from a remote URL (GitHub, Google Drive, etc.)
    and returns the local path to the temporary file.
    """
    # 1. Handle Google Drive URLs (convert to direct download)
    if "drive.google.com" in url:
        if "/file/d/" in url:
            file_id = url.split("/file/d/")[1].split("/")[0]
            url = f"https://drive.google.com/uc?export=download&id={file_id}"
        elif "id=" in url:
            file_id = url.split("id=")[1].split("&")[0]
            url = f"https://drive.google.com/uc?export=download&id={file_id}"

    # 2. Handle GitHub URLs (convert to raw if needed)
    if "github.com" in url and "/blob/" in url:
        url = url.replace("github.com", "raw.githubusercontent.com").replace(
            "/blob/", "/"
        )

    # 3. Download the file
    try:
        response = httpx.get(url, follow_redirects=True)
        response.raise_for_status()

        # Check content type if possible
        content_type = response.headers.get("Content-Type", "").lower()
        is_pdf = "pdf" in content_type or url.lower().endswith(".pdf")

        # Google Drive direct links often return application/octet-stream
        if not is_pdf and "drive.google.com" not in url:
            print(f"⚠️ Warning: URL might not be a PDF (Content-Type: {content_type})")

        if "drive.google.com" in url and "octet-stream" in content_type:
            # Assume it's a PDF if we targeted it as such
            pass

        # Create temporary file
        fd, temp_path = tempfile.mkstemp(suffix=".pdf")
        with os.fdopen(fd, "wb") as f:
            f.write(response.content)

        return temp_path
    except Exception as e:
        raise RuntimeError(f"Failed to download PDF from {url}: {str(e)}")
