# Automaton Auditor Swarm Master Plan

## 🎯 Goal Description

Building a hierarchical multi-agent swarm using LangGraph to audit GitHub repositories and PDF reports based on a forensic rubric. The system features a digital courtroom architecture with Detectives, Judges, and a Supreme Court.

---

## 🚀 TenX Features & Bonuses

- **Batch Processing**: Support for up to 3 URLs processed sequentially/parallel.
- **Dockerfile**: Containerized runtime for consistency.
- **Checkpointers**: State persistence for long-running audits.
- **Dynamic Rubric Loading**: Update `rubric.json` without redeploying.
- **AST Parsing**: Deep code analysis with `tree-sitter`.
- **RAG-lite for PDFs**: Semantic chunking and search.

---

## 🏛️ Digital Courtroom Architecture

### Environment Isolation (Mandatory)

The system is strictly separated into two virtual environments due to dependency constraints (CUDA/Torch vs Orchestration):

1. **Core Environment** (`envs/core`): Runs LangGraph, Judges, Detectives (excluding DocAnalyst).
2. **Docling Environment** (`envs/docling`): Isolated ML-heavy runtime for parsing PDFs, invoked via subprocess.

### Layer 1: Detectives (Forensic Sub-Agents)

- **RepoInvestigator**: Code analysis via AST and Git forensic analysis.
- **DocAnalyst**: PDF content verification and cross-referencing.
- **VisionInspector**: Diagram analysis for architectural flow verification.

### Layer 2: Judges (The Dialectical Bench)

- **Prosecutor**: Critical lens, focuses on gaps and security flaws.
- **Defense**: Optimistic lens, rewards effort and architectural intent.
- **Tech Lead**: Pragmatic lens, evaluates maintainability and technical debt.

### Layer 3: Supreme Court (Synthesis Engine)

- **Chief Justice**: Deterministic conflict resolution and final verdict.

---

## ✅ Task Checklist & Branching Strategy

### 🟢 Phase 1: Planning & Infrastructure

| Task                                              | Branch               | Status |
| :------------------------------------------------ | :------------------- | :----- |
| Initialize project with `uv` and `pyproject.toml` | `main`               | [x]    |
| Configure environment variables & LangSmith       | `main`               | [x]    |
| Setup pre-commit hooks                            | `main`               | [x]    |
| Implement dynamic `rubric.json` loader            | `feat/rubric-loader` | [x]    |

### 🔵 Phase 2: Core Development

| Task                                                 | Branch                | Status |
| :--------------------------------------------------- | :-------------------- | :----- |
| **State & Models**: Define Pydantic models & tests   | `feat/state-models`   | [/]    |
| **Forensic Tools**: Implement AST & Git tools        | `feat/forensic-tools` | [ ]    |
| **Layer 1 (Detectives)**: Implement parallel nodes   | `feat/detectives`     | [ ]    |
| **Layer 2 (Judges)**: Implement 3 personas & prompts | `feat/judges`         | [ ]    |
| **Layer 3 (Justice)**: ChiefJusticeNode & synthesis  | `feat/justice`        | [ ]    |

### 🟡 Phase 3: Orchestration & Wiring

| Task                                         | Branch                     | Status |
| :------------------------------------------- | :------------------------- | :----- |
| Define `StateGraph` with Parallel Fan-Out/In | `feat/graph-orchestration` | [ ]    |
| Implement structured output enforcement      | `feat/structured-output`   | [ ]    |
| Setup Git sandboxing using `tempfile`        | `feat/sandbox-git`         | [ ]    |

### 🟠 Phase 4: Advanced Features

| Task                                    | Branch                  | Status |
| :-------------------------------------- | :---------------------- | :----- |
| Implement Checkpointers for persistence | `feat/checkpointers`    | [ ]    |
| Implement Batch Processing (3 URLs)     | `feat/batch-processing` | [ ]    |
| Create production `Dockerfile`          | `feat/docker`           | [ ]    |

### 🔴 Phase 5: Verification & Submission

| Task                              | Branch                  | Status |
| :-------------------------------- | :---------------------- | :----- |
| Run audits on self/peer codebases | `feat/audit-execution`  | [ ]    |
| Generate Markdown Audit Reports   | `feat/reporting`        | [ ]    |
| Create `SELF_IMPROVEMENT.md`      | `feat/self-improvement` | [ ]    |

---

## 🧪 Verification Plan

### Automated Tests

- Verify AST parsing extracts correct class/function signatures.
- Validate structured output from all judge nodes.
- Test parallel execution of detectives and judges.

### Manual Verification

- Inspect generated markdown reports for nuance and accuracy.
- Review LangSmith traces for "Judicial Debates".
