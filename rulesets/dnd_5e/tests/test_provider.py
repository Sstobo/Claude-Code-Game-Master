"""Provider skeleton tests — Phase 1 placeholder behavior."""
import pytest

from lib import ruleset
import rulesets.dnd_5e  # noqa: F401 — registers DnD5eRuleset
from rulesets.dnd_5e.provider import DnD5eRuleset


def test_import_registers_dnd5e_provider():
    p = ruleset.get()
    assert isinstance(p, DnD5eRuleset)
    assert p.name == "dnd_5e"


def test_placeholder_methods_raise_not_implemented():
    p = DnD5eRuleset()
    with pytest.raises(NotImplementedError):
        p.init_sheet({})
