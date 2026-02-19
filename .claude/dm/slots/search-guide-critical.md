## Search Guide (CRITICAL)

**All tool calls MUST use `bash tools/` prefix.** Never call bare `dm-search.sh`.

### Choosing the Right Search Tool

| I need to... | Use this |
|--------------|----------|
| Search source material (books/PDFs) for any topic | `bash tools/dm-search.sh "query" --rag-only` |
| Search world state (NPCs, locations, facts, plots) | `bash tools/dm-search.sh "query" --world-only` |
| Search both world state AND source material | `bash tools/dm-search.sh "query"` |
| Get RAG passages for a **known entity by name** | `bash tools/dm-enhance.sh query "Entity Name"` |
| Get scene context for current location | `bash tools/dm-enhance.sh scene "Location Name"` |
| Search NPCs by location/quest tag | `bash tools/dm-search.sh --tag-location "Place"` |

### Common Mistakes

- **WRONG**: `dm-enhance.sh query "some free text search"` — This does entity NAME lookup, not free-text search. It will fail if no entity matches the name.
- **RIGHT**: `bash tools/dm-search.sh "some free text search" --rag-only` — This does free-text vector search across all source material.
- **WRONG**: `dm-search.sh "query"` — Missing `bash tools/` prefix. Will error with "command not found".
- **RIGHT**: `bash tools/dm-search.sh "query"` — Always use the full prefix.

### When to Use Each

- **`dm-search.sh --rag-only`**: Looking for items, events, lore, dialogue, or anything from the source books. Free-text, works with any query.
- **`dm-enhance.sh query`**: You know an NPC/location/item name and want passages specifically about that entity. The name must match (fuzzy matching applies).
- **`dm-enhance.sh scene`**: You're narrating a location and want DM-internal context from source material. Auto-called by `dm-session.sh start/move`.

---
