"""Tests for enhancer-relevance-gate: _gate_passages, query shape, batch honesty."""

from lib.entity_enhancer import EntityEnhancer


def _p(text, distance):
    return {"text": text, "distance": distance}


def test_name_bearing_force_included_even_above_floor():
    # A passage that names the entity but has poor (high) distance must survive.
    passages = [
        _p("Hekla raised her crossbow.", 1.4),   # names entity, above 1.0 floor
        _p("unrelated scenery prose", 0.3),       # close but no name
    ]
    kept, frac = EntityEnhancer._gate_passages("Hekla", [], passages, floor=1.0, keep_target=4)
    texts = [p["text"] for p in kept]
    assert "Hekla raised her crossbow." in texts, "name-bearing passage must be force-included"
    assert frac > 0


def test_below_floor_non_name_passages_dropped_not_padded():
    passages = [
        _p("Hekla spoke.", 0.4),          # name-bearing
        _p("far-off noise", 1.3),         # no name, above floor -> dropped
        _p("more noise", 1.6),            # no name, above floor -> dropped
    ]
    kept, frac = EntityEnhancer._gate_passages("Hekla", [], passages, floor=1.0, keep_target=4)
    assert len(kept) == 1, "should NOT pad with below-floor noise"
    assert frac == 1.0


def test_zero_name_bearing_attaches_nothing():
    passages = [_p("a passage about someone else", 0.5), _p("another", 0.6)]
    kept, frac = EntityEnhancer._gate_passages("Tserendolgor", [], passages, floor=1.0)
    assert kept == [], "0 name-bearing → nothing attached"
    assert frac == 0.0


def test_aliases_count_as_name_bearing():
    passages = [_p("Princess Donut shrieked.", 0.7)]
    kept, frac = EntityEnhancer._gate_passages("Donut", ["Princess Donut"], passages, floor=1.0)
    assert frac == 1.0


def test_fill_respects_floor_and_target():
    passages = [
        _p("Carl did a thing.", 0.2),     # name
        _p("close scene A", 0.5),         # under floor
        _p("close scene B", 0.9),         # under floor
        _p("close scene C", 0.95),        # under floor (would exceed target)
    ]
    kept, frac = EntityEnhancer._gate_passages("Carl", [], passages, floor=1.0, keep_target=3)
    # 1 name-bearing + fill to target 3 => 3 total, lowest-distance others first
    assert len(kept) == 3
    assert kept[0]["distance"] == 0.2


def test_enhancement_queries_include_type_not_name_alone():
    # Criterion 3: no live corpus in this suite; assert the query is richer than name-only.
    queries = EntityEnhancer._enhancement_queries("Hekla", "npc")
    assert queries[0] != "Hekla"
    assert "Hekla" in queries[0]
    assert "npc" in queries[0]
    assert any("Hekla" in q and "npc" in q for q in queries)


def _stub_enhancer(unenhanced, passages_by_name):
    enhancer = EntityEnhancer.__new__(EntityEnhancer)
    enhancer.list_unenhanced = lambda entity_type=None: list(unenhanced)
    enhancer.query_passages = lambda name, entity_type, n_results=8: list(
        passages_by_name.get(name, [])
    )
    enhancer.find_entity = lambda name: {"type": "npc", "name": name, "data": {}}
    applied = []

    def apply(etype, name, context, new_description=None, additional_fields=None):
        applied.append({"name": name, "context": context, "fields": additional_fields})
        return True

    enhancer.apply_enhancements = apply
    return enhancer, applied


def test_zero_name_bearing_batch_reports_not_enhanced():
    enhancer, applied = _stub_enhancer(
        [{"type": "npc", "name": "Ghost"}],
        {"Ghost": [_p("a passage about someone else", 0.4)]},
    )
    result = enhancer.batch_enhance()
    assert applied == []
    assert result["enhanced"] == 0
    assert result["low_relevance"] == 1
    assert result["skipped"] == 0
    assert result["low_relevance_names"] == ["Ghost"]


def test_name_bearing_batch_still_enhances():
    enhancer, applied = _stub_enhancer(
        [{"type": "npc", "name": "Hekla"}],
        {"Hekla": [_p("Hekla raised her crossbow.", 0.3)]},
    )
    result = enhancer.batch_enhance()
    assert len(applied) == 1
    assert applied[0]["name"] == "Hekla"
    assert result["enhanced"] == 1
    assert result["low_relevance"] == 0


def test_batch_summary_warns_and_nonzero_above_threshold():
    result = {
        "enhanced": 1,
        "skipped": 0,
        "low_relevance": 2,
        "low_relevance_names": ["A", "B"],
        "total": 3,
    }
    text, code = EntityEnhancer.format_batch_summary(result)
    assert code != 0
    assert "WARNING" in text
    assert "A" in text and "B" in text
    assert "not attached" in text


def test_batch_summary_quiet_under_threshold():
    result = {
        "enhanced": 4,
        "skipped": 0,
        "low_relevance": 0,
        "low_relevance_names": [],
        "total": 4,
    }
    text, code = EntityEnhancer.format_batch_summary(result)
    assert code == 0
    assert "WARNING" not in text
