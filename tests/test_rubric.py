import pytest
import os
import json
from src.utils import load_rubric, get_dimension_by_id

def test_load_rubric_success(tmp_path):
    # Create a dummy rubric file
    rubric_data = {
        "rubric_metadata": {"version": "1.0.0"},
        "dimensions": [{"id": "test_dim", "name": "Test Dimension"}]
    }
    rubric_file = tmp_path / "test_rubric.json"
    rubric_file.write_text(json.dumps(rubric_data))
    
    loaded = load_rubric(str(rubric_file))
    assert loaded["rubric_metadata"]["version"] == "1.0.0"
    assert len(loaded["dimensions"]) == 1

def test_load_rubric_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_rubric("non_existent_file.json")

def test_get_dimension_by_id():
    rubric = {
        "dimensions": [
            {"id": "dim1", "name": "Name 1"},
            {"id": "dim2", "name": "Name 2"}
        ]
    }
    dim = get_dimension_by_id(rubric, "dim2")
    assert dim["name"] == "Name 2"
    
    with pytest.raises(ValueError):
        get_dimension_by_id(rubric, "dim3")
