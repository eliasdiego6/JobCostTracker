# Prompt log

Every work request is saved here before any work starts, for traceability.

**Naming:** `YYYY-MM-DD_NN_short-slug.md`. `NN` counts up within the day (`01`, `02`, …); the slug is
2–4 lowercase words joined by hyphens. Example: `2026-10-23_01_foundation-scaffold.md`.

**Process:** log → clarify → plan → approve → implement → record. Code/schema changes run through the
three-agent pipeline. See [CLAUDE.md](../CLAUDE.md).

## Template

```markdown
# YYYY-MM-DD #NN — Title

| Field | Value |
|---|---|
| Date | YYYY-MM-DD |
| Requested by | |
| Status | Plan written — awaiting approval / Approved — in progress / Done / Dropped |
| Starting commit | |

## Request (verbatim)

> ...

## Context
What exists today that matters for this request.

## Clarifying questions
1. ...

## Plan
Steps, what changes, what doesn't, how it will be verified.

## PM brief
(Pipeline tasks) the project-manager agent's final brief.

## Decisions
Answers to the questions and the approval (who, when).

## Programmer report
(Pipeline tasks) each round's report from the programmer agent.

## QC verdicts
(Pipeline tasks) each round's PASS/FAIL from the qc-reviewer agent.

## Outcome
What was done, test results, commit(s), memory entry, follow-ups.
```

## Index

| Date | # | Title | Status |
|---|---|---|---|
| 2026-10-23 | 01 | [Foundation scaffold](2026-10-23_01_foundation-scaffold.md) | Done |
| 2026-10-23 | 02 | [Real QB connector + Settings](2026-10-23_02_real-qb-phase.md) | Paused |
| 2026-10-23 | 03 | [CLAUDE.md rules + agent pipeline](2026-10-23_03_claude-md-agent-pipeline.md) | Done |
| 2026-10-23 | 04 | [Consolidated open questions + roadmap](2026-10-23_04_open-questions.md) | Done |
