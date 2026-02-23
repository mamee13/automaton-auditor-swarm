import json
from pathlib import ROOT_DIR
from typing import Dict, Any

def load_rubric(file_path: str = "rubric/week2_rubric.json") -> Dict[str, Any]:
    """
    Loads the machine-readable rubric from a JSON file.
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Rubric file not found at {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding rubric JSON: {str(e)}")

def get_dimension_by_id(rubric: Dict[str, Any], dimension_id: str) -> Dict[str, Any]:
    """
    Retrieves a specific dimension from the loaded rubric.
    """
    for dimension in rubric.get("dimensions", []):
        if dimension.get("id") == dimension_id:
            return dimension
    raise ValueError(f"Dimension ID '{dimension_id}' not found in rubric")
