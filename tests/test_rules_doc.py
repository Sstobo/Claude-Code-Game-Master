"""Tests for rules-doc-authoring: set_rules_doc pointer + WorldKit resolution."""

import json
from pathlib import Path

from lib.overview_seed import set_rules_doc


def test_set_rules_doc_points_when_file_exists(tmp_path):
    (tmp_path / "rules.md").write_text("# rules")
    (tmp_path / "ruleset.json").write_text(json.dumps({"name": "K", "rules_doc": None}))
    r = set_rules_doc(str(tmp_path), "rules.md")
    assert r["rules_doc"] == "rules.md" and r["changed"] is True
    assert json.loads((tmp_path / "ruleset.json").read_text())["rules_doc"] == "rules.md"


def test_set_rules_doc_noop_when_file_missing(tmp_path):
    (tmp_path / "ruleset.json").write_text(json.dumps({"name": "K", "rules_doc": None}))
    r = set_rules_doc(str(tmp_path), "rules.md")  # no rules.md on disk
    assert r["changed"] is False
    assert json.loads((tmp_path / "ruleset.json").read_text())["rules_doc"] is None


def test_worldkit_resolves_rules_doc(dcc_world):
    from lib.world_kit import WorldKit
    camp = Path(dcc_world) / "campaigns" / "dungeon-crawler-carl"
    (camp / "rules.md").write_text("# DCC rules\nViewers, not XP.")
    rs = json.loads((camp / "ruleset.json").read_text())
    rs["rules_doc"] = "rules.md"
    (camp / "ruleset.json").write_text(json.dumps(rs))
    # active campaign in dcc_world is dungeon-crawler-carl
    assert WorldKit(dcc_world).rules_doc_path() is not None
