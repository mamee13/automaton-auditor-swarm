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

## ✅ Task Checklist

### 1. Planning & Infrastructure

- [ ] Initialize project with `uv` and `pyproject.toml`
- [ ] Configure environment variables and LangSmith tracing
- [ ] Implement dynamic `rubric.json` loader

### 2. Core Development

- [ ] **State & Models**: Define Pydantic models for `AgentState`, `Evidence`, `JudicialOpinion`.
- [ ] **Layer 1 (Detectives)**: Implement parallel nodes for Repo, Doc, and Vision investigators.
- [ ] **Layer 2 (Judges)**: Implement Prosecutor, Defense, and Tech Lead personas with distinct prompts.
- [ ] **Layer 3 (Justice)**: Implement `ChiefJusticeNode` with deterministic synthesis.

### 3. Orchestration & Wiring

- [ ] Define LangGraph `StateGraph` with parallel Fan-Out/Fan-In.
- [ ] Implement structured output enforcement (Pydantic validation).
- [ ] Setup Git sandboxing using `tempfile`.

### 4. Advanced Features

- [ ] Implement Batch Processing for multiple URLs.
- [ ] Implement Checkpointers for state persistence.
- [ ] Create `Dockerfile`.

### 5. Verification & Submission

- [ ] Run audits on self/peer codebases.
- [ ] Generate Markdown Audit Reports.
- [ ] Create `SELF_IMPROVEMENT.md`.

---

## 🧪 Verification Plan

### Automated Tests

- Verify AST parsing extracts correct class/function signatures.
- Validate structured output from all judge nodes.
- Test parallel execution of detectives and judges.

### Manual Verification

- Inspect generated markdown reports for nuance and accuracy.
- Review LangSmith traces for "Judicial Debates".
