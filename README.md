# ⚖️ Automaton Auditor Swarm

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)

The **Automaton Auditor Swarm** is a hierarchical multi-agent system built on LangGraph designed to forensically audit GitHub repositories and PDF reports. Modeled after a **Digital Courtroom**, it employs adversarial personas and deterministic protocol synthesis to provide objective, high-integrity evaluations.

---

## 🏛️ Architecture: The Digital Courtroom

The system operates in three distinct layers, ensuring a dialectical approach to auditing:

### 1. Detective Layer (Parallel Evidence Collection)

Three specialized sub-agents run in parallel to gather structured evidence:

- **RepoInvestigator**: Deep code analysis using `tree-sitter` AST parsing and Git history forensics.
- **DocAnalyst**: PDF report analysis using a RAG-lite approach with `Docling` for semantic extraction.
- **VisionInspector**: Multimodal analysis of architectural diagrams and UI screenshots.

### 2. Judicial Layer (Adversarial Analysis)

The gathered evidence is presented to three judges with biased personas:

- **Prosecutor**: Focused on "Vibe Coding" detection, architectural fraud, and security loopholes.
- **Defense**: Searches for technical sophistication, intent, and documentation depth.
- **Tech Lead**: Evaluates pragmatic maintainability, dependency health, and engineering rigor.

### 3. Supreme Court (Conflict Resolution)

The **Chief Justice** applies **Protocol B**—a set of deterministic rules to resolve disagreements:

- **Security Override**: Confirmed security flaws cap the final score regardless of other merits.
- **Fact Supremacy**: Directly contradicts claims if evidence proves them false.
- **Tech Lead Weighting**: Architecture scores are weighted toward the Tech Lead's expertise.
- **Dissent Summary**: Every report includes a summary of judicial disagreements for transparency.

---

## 🚀 Key Features

- **Parallel Orchestration**: High-speed audit execution using LangGraph fan-out/fan-in patterns.
- **Batch Processing**: Audit up to 3 URLs/PDF pairs sequentially in a single run.
- **AST Parsing**: Moving beyond regex to verify semantic code constructs with `tree-sitter`.
- **Environment Isolation**: Isolated `uv` environments for Core Orchestration and ML-heavy Docling processing.
- **Checkpointers**: Built-in state persistence for long-running audit cycles.
- **Multimodal Vision**: Automated diagram verification via GPT-4o Vision.

---

## 🛠️ Installation & Setup

### Prerequisites

- **Python 3.12+**
- **uv** (Recommended) or `pip`
- **OpenAI API Key** (for Judges and Vision)

### Environment Setup

The project uses two separate environments to avoid dependency conflicts:

1. **Core Environment**:

   ```bash
   uv sync --frozen
   ```

2. **Docling Environment**:
   ```bash
   uv sync --frozen --group docling
   ```
   _(Note: This is managed automatically by the `DocAnalyst` via subprocess bridges)._

### Configuration

Create a `.env` file from the template:

```bash
cp .env.example .env
# Add your OPENAI_API_KEY and LANGSMITH_API_KEY (optional)
```

---

## 📖 Usage

Run the auditor via the main entry point:

```bash
uv run main.py --repo <GITHUB_URL> --report <PDF_PATH>
```

For batch processing multiple repositories:

```bash
uv run main.py --batch config/batch_audits.json
```

---

## 🧪 Testing

The system includes a comprehensive test suite for AST forensics, state management, and judicial reasoning.

```bash
# Run all tests
uv run pytest

# Run specific forensic tests
uv run pytest tests/test_forensics.py
```

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
