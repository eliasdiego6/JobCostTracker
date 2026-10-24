# 2026-10-23 #02 — Next phase: real QuickBooks connector + Settings

| Field | Value |
|---|---|
| Date | 2026-10-23 |
| Requested by | EPerez |
| Status | **Paused**: interrupted before answers by #03 (CLAUDE.md rules + agent pipeline). Resume through the new pipeline. |
| Starting commit | `603a6f1` (branch `foundation-scaffold`) |

## Request (verbatim)

> I am ready for the next phase. Do you have any questions before getting started? An approved plan
> is required before getting started.

## Context

- The "next phase" per PLAN.md and docs/MEMORY.md: discovery results → real `DesktopConnector`
  (`app/qb/desktop.py`) + Settings screen for the account → bucket mapping (PLAN steps 2–3).
- `scripts/qb_discover.py` exists but has not been run against the real company file; no
  `discovery_output/` exists on the dev PC.
- The discovery output answers the design questions the connector depends on: QB edition and version
  (32- vs 64-bit SDK), where the job number lives (job name vs custom field), how labor is posted
  (paychecks, journal entries, items), and whether materials and subs share accounts. Shared accounts
  would mean mapping by item, not only by account.
- Already in place: the qbXML request builders and parsers (tested offline), the `Connector` Protocol,
  the connector contract test, the `account_map` table and its repository functions.

## Clarifying questions

1. Has the discovery script been run on the server, and can its `summary.txt` be shared?
2. Scope of this phase: Settings screen, real connector, or both?
3. Who may change the account → bucket mapping, given that it changes every job's numbers?
4. Should mapping by item be supported in addition to mapping by account?

## Decisions

_Pending._

## Plan

_To be written after the answers._

## Outcome

_Pending._
