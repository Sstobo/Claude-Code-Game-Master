"""Contract tests for the lib.ruleset registry."""
import pytest

from lib import ruleset


@pytest.fixture
def _clear_provider():
    """Clear _provider to None before test, restore after.

    Originally autouse=True; converted to explicit fixture now that
    tests/conftest.py's _snapshot_ruleset_provider handles session-level
    snapshotting. test_bootstrap_registers_dnd5e_by_default must NOT clear
    the provider — it verifies the session-start bootstrap state.
    """
    saved = ruleset._provider
    ruleset._provider = None
    yield
    ruleset._provider = saved


class _StubProvider:
    name = "stub"

    # Methods are not exercised here — Protocol is structural.
    def init_sheet(self, npc_data): ...
    def update_hp(self, sheet, delta): ...
    def set_field(self, sheet, field, value): ...
    def format_npc_sheet(self, npc_data): ...
    def format_party_summary(self, party): ...
    def format_character_block(self, character): ...
    def format_party_context_block(self, party, full): ...
    def normalize_advancement(self, char): ...
    def advance(self, char, amount): ...
    def advancement_status(self, char): ...
    def format_character_summary(self, char): ...
    def validate_ability(self, ability): ...
    def validate_skill(self, s): ...
    def validate_alignment(self, a): ...
    def validate_condition(self, c): ...
    def validate_damage_type(self, d): ...


def test_get_without_register_raises_runtime_error(_clear_provider):
    with pytest.raises(RuntimeError, match="No ruleset registered"):
        ruleset.get()


def test_is_registered_reflects_state(_clear_provider):
    assert ruleset.is_registered() is False
    ruleset.register(_StubProvider())
    assert ruleset.is_registered() is True


def test_register_then_get_returns_provider(_clear_provider):
    p = _StubProvider()
    ruleset.register(p)
    assert ruleset.get() is p


def test_re_register_replaces_provider(_clear_provider):
    p1 = _StubProvider()
    p2 = _StubProvider()
    ruleset.register(p1)
    ruleset.register(p2)
    assert ruleset.get() is p2


def test_bootstrap_registers_dnd5e_by_default():
    """After plain `import lib`, the default DnD5e provider is registered.

    The autouse fixture in tests/conftest.py preserves whatever was registered
    at session start.
    """
    import lib  # noqa: F401
    from rulesets.dnd_5e.provider import DnD5eRuleset
    assert ruleset.is_registered()
    assert isinstance(ruleset.get(), DnD5eRuleset)
