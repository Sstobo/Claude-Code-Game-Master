"""Phase 5: NPC extraction schema uses opaque `stats` instead of fixed `hp`."""
from lib import extraction_schemas


def test_npc_schema_uses_opaque_stats():
    schema = extraction_schemas.NPC_SCHEMA
    assert isinstance(schema['stats'], dict)
    assert 'hp' not in schema['stats']
    # Old 5E-shaped keys (ac/hp/cr/abilities) should be gone from the schema
    # template. Extractors emit whatever they find under `stats`.


def test_npc_schema_top_level_keys_unchanged():
    schema = extraction_schemas.NPC_SCHEMA
    for k in ('name', 'description', 'attitude',
              'location_tags', 'events', 'stats',
              'dialogue', 'source'):
        assert k in schema
