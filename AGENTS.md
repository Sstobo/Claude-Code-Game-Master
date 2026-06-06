# AGENTS

Project agent guidance. The full DM ruleset and runtime behavior live in `CLAUDE.md`.

## Tickets

The `tickets/` folder is the single source of truth for all work. Each ticket is
a markdown file whose status is its parent folder and whose slug is its filename.

Do NOT use GitHub Issues, Linear, Notion, chat history, or memory as the work
queue. Do NOT scatter TODOs across the codebase.

When the user mentions tickets, todos, queue, next up, kanban, backlog, ready
work, triage, incoming bugs, or classifying an issue — inspect `tickets/` before
answering:

    ls tickets/*/                          # board at a glance
    grep -H priority: tickets/ready/*.md   # ready AFK queue

List filenames and read frontmatter when surveying. Never dump full ticket
bodies for the whole board — `cat` only the one ticket you are about to act on.

A status transition is `git mv tickets/<from>/<slug>.md tickets/<to>/<slug>.md`
plus a frontmatter + History edit. Claiming a ticket is moving it from `ready/`
to `in-progress/`; a failed move means another agent claimed it first.
