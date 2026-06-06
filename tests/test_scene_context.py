"""Tests for scene-context-consolidation.

One unified entry replaces the dm-search / dm-enhance-query / dm-enhance-scene
trio. World-state context is always returned; RAG passages are optional and must
degrade gracefully when a campaign has no vector store (the test fixture omits the
12M vectors/ dir on purpose). Live grounded-passage behavior is smoke-verified in
the ticket QA against the DCC campaign that has vectors.
"""

from lib.scene_context import SceneContext


def test_structure_and_graceful_without_rag(dcc_world):
    sc = SceneContext(dcc_world).build("Over City Village")
    for key in ("location", "world", "entities", "passages", "rag_available"):
        assert key in sc
    assert isinstance(sc["passages"], list)
    # Fixture has no vectors/ -> RAG unavailable, but the call must not crash.
    assert sc["rag_available"] is False
    assert sc["passages"] == []


def test_resolves_named_entity_from_world_state(dcc_world):
    sc = SceneContext(dcc_world).build("Tutorial Guild Hall", entities=["Mordecai"])
    assert "Mordecai" in sc["entities"]
    assert sc["entities"]["Mordecai"] is not None


def test_defaults_to_current_location(dcc_world):
    built = SceneContext(dcc_world).build()  # no location -> resolve current
    assert built["location"], "current location should resolve from campaign-overview"
