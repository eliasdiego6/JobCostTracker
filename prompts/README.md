# Prompt log

Every work request is saved here before any work starts, for traceability.

**Naming:** `YYYY-MM-DD_NN_short-slug.md`. `NN` counts up within the day (`01`, `02`, …); the slug is
2–4 lowercase words joined by hyphens. Example: `2026-10-23_01_foundation-scaffold.md`.

**Process:** log → clarify → plan → approve → implement → record. See `docs/CONVENTIONS.md`.

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

## Decisions
Answers to the questions and the approval (who, when).

## Outcome
What was done, test results, commit(s), memory entry, follow-ups.
```

## Index

| Date | # | Title | Status |
|---|---|---|---|
| 2026-10-23 | 01 | [Foundation scaffold](2026-10-23_01_foundation-scaffold.md) | Done |
