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

### 📋 Prerequisites

To replicate the deterministic environment exactly, ensure the following are installed:

- **Python**: `3.12` or higher (Managed via `uv` or `pyenv`).
- **uv**: Latest version (The project's deterministic package manager).
- **Git**: Required for repository forensic cloning.
- **System Build Tools**: `gcc` / `make` (Required for compiling `tree-sitter` bindings).
- **OpenAI API Key**: Required for Judicial and Vision nodes.

### ⚙️ Environment Setup

Extract the following variables into a `.env` file from the provided template:

```bash
cp .env.example .env
# Open .env and fill in your API keys (OPENAI_API_KEY is mandatory)
```

### 📦 Dependency Management

The project uses two separate, isolated environments to prevent dependency conflicts between LangGraph and ML-heavy libraries:

1. **Install Core Environment** (Orchestration, Judges, Basic Detectives):

   ```bash
   uv sync --frozen
   ```

2. **Install Docling Environment** (PDF Analysis):
   ```bash
   # Use the --group flag to include docling-specific dependencies
   uv sync --frozen --group docling
   ```
   _Note: The `DocAnalyst` automatically invokes the correct interpreter from `envs/docling` via a subprocess bridge._

---

## 📖 Usage

### Run a Self-Audit

Use the `--onself` flag to audit your own repository. This will use the default repository link configured in `main.py`.

```bash
uv run main.py --onself
```

> [!TIP]
> **To use your own repository for self-audits:**
> Update the `batch_urls` assignment in `main.py` (Line 49) with your GitHub URL.

### Run a Peer-Audit

To audit another repository, you must provide the **GitHub Repository URL**. You can optionally provide a **PDF Audit Report** for a more comprehensive forensic comparison.

```bash
uv run main.py --repo <PEER_GITHUB_URL> [--report <PEER_PDF_REPORT_PATH>]
```

- **`--repo`**: The link to the repository you wish to audit.
- **`--report`** (Optional): The path or **URL** (Google Drive, GitHub, etc.) to the peer's PDF audit report. If provided, the system will automatically download and compare the code findings against the claims in the report.

### Batch Processing

Audit multiple repositories sequentially by providing a JSON file with a list of URLs.

```bash
uv run main.py --batch config/batch_audits.json
```

The `config/batch_audits.json` file should look like this:

```json
["https://github.com/user/repo-one", "https://github.com/user/repo-two"]
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
