import os
from src.tools.forensics import analyze_git_history, parse_ast_for_forensics


def test_forensics():
    # Test AST parsing on this very file or src/state.py
    print("--- AST Forensics Test ---")
    file_to_test = "src/state.py"
    if os.path.exists(file_to_test):
        res = parse_ast_for_forensics(file_to_test)
        print(f"Results for {file_to_test}:")
        print(f"Classes: {res.get('classes')}")
        print(f"Functions: {res.get('functions')}")
        print(f"Pydantic Score: {res.get('pydantic_score')}")
    else:
        print(f"File {file_to_test} not found.")

    # Test Git analysis on the current repo
    print("\n--- Git History Test ---")
    res = analyze_git_history(".")
    print(f"Commit Count: {res.get('commit_count')}")
    print(f"Author Count: {res.get('author_count')}")
    print(f"Latest Commit: {res.get('latest_commit')}")


if __name__ == "__main__":
    test_forensics()
