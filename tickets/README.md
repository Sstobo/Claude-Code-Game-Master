# Tickets

This folder is the single source of truth for all work. Each ticket is one
markdown file. Its **status is the folder it lives in**; its **slug is its
filename**. Moving a file between folders is a status transition.

## Folders

- `needs-triage/` `needs-info/` — intake and underspecified work
- `ready/` — triaged, grabbable work
- `in-progress/` — claimed by an agent
- `in-review/` — HITL ticket awaiting human sign-off
- `done/` — verified and committed
- `blocked/` `regression/` `wontfix/` — stuck, failed QA, rejected
- `prds/` `research/` `.out-of-scope/` — supporting artifacts
- `progress.md` — append-only cross-ticket timeline

## Working the board

    ls tickets/*/                       # board at a glance
    grep -H priority: tickets/ready/*.md  # ready queue
    git mv tickets/ready/x.md tickets/in-progress/x.md   # claim

Frontmatter (priority, kind, lane, blockedBy, claimedBy, resolution) lives at
the top of each file. Acceptance criteria live in the body and are the QA
source of truth. Do NOT use GitHub Issues, Linear, Notion, or memory as the
queue — this folder is it.
