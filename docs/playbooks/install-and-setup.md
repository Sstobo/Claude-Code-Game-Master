---
type: Playbook
title: Install and setup
description: Getting from a clean machine to a playable harness, which dependencies are actually optional, and every environment variable the code reads.
sources:
  - { resource: /install.sh }
  - { resource: /pyproject.toml }
  - { resource: /.claude/commands/setup.md }
generated: { by: claude-opus-5, at: 2026-08-13T13:52:08Z }
---

# Install and setup

```bash
./install.sh          # interactive; prompts for which extras
./install.sh --auto   # non-interactive, --all-extras
```

`install.sh` is zero-to-hero: it installs Homebrew (macOS), Python 3.11+, `uv`, `jq`, and
the project dependencies. `/setup` is the lighter in-session repair path — venv, deps,
`.env`, `chmod`, and a `lib/dice.py "1d20"` smoke test.

Verify the install the way the harness itself does:

```bash
[ -d ".venv" ] && uv run python -c "import anthropic"
```

That check failing is what routes a session to `/setup` before it greets you.

## Which dependency groups matter

| Extra | Contains | Missing it means |
|---|---|---|
| *(core)* | `pdfplumber`, `pypdf2`, `python-docx`, `python-dotenv`, `requests`, `anthropic` | nothing works |
| `rag` | `sentence-transformers`, `chromadb` | **`/import` cannot vectorize**, and every source-passage lookup silently returns empty |
| `voice` | `elevenlabs` | nothing — see below |
| `dev` | `pytest`, `black`, `ruff`, `mypy`, `pre-commit` | can't run the suite |

`rag` is the one that changes behaviour rather than failing loudly: retrieval degrades to
empty rather than erroring, so a campaign imported without it looks like a book with
nothing in it. See [RAG stack](../modules/rag-stack.md). Its first run downloads roughly
500MB of model files.

**Two declared dependencies have no importer in the codebase:** `anthropic` (core) and
`elevenlabs` (the `voice` extra). Verified 2026-08-13 — no `import anthropic` or
`elevenlabs` anywhere in `lib/`, `tools/`, or `features/`. The harness runs *inside* Claude
Code, so play needs no API key of its own; `anthropic` survives as the venv-health probe
the startup check uses, and `voice` is a declared-but-unimplemented feature. Re-derive with
`grep -rn "import anthropic" lib/ tools/ features/` rather than trusting this line.

## Every environment variable the code reads

Enumerated from `os.environ.get` across `lib/` and `tools/`:

| Variable | Read by | Effect |
|---|---|---|
| `OPENAI_API_KEY` | `image_gen`, `session_manager` | the **only** gate on scene images. Absent → the session brief says DISABLED |
| `OPENAI_IMAGE_MODEL` | `image_gen` | default `gpt-image-2` |
| `OPENAI_IMAGE_QUALITY` | `image_gen` | default `medium` |
| `OPENAI_IMAGE_SIZE` | `image_gen` | default `1536x1024` |
| `DM_JSON=1` | `cli_output` | forces the `--json` envelope globally |
| `DM_DEBUG_CONTEXT=1` | `session_manager` | prints an approximate context token count to stderr |

The `.env` that `/setup` writes contains only `DEFAULT_CAMPAIGN_NAME` and
`DEFAULT_STARTING_LOCATION` — neither of which appears in the table above. Add
`OPENAI_API_KEY` by hand to turn images on.

## Python is always `uv run python`

`common.sh` resolves the interpreter once, preferring `uv`. Calling bare `python` /
`python3` bypasses the venv and will fail on any RAG import. See
[the tool wrapper contract](../conventions/tool-wrapper-contract.md).

## Related

- [Testing](testing.md)
- [Illustrating a scene](../flows/scene-illustration.md) — what `OPENAI_API_KEY` unlocks
