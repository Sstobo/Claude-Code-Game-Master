"""Contract tests for the lib.ruleset registry."""
import pytest

from lib import ruleset


@pytest.fixture(autouse=True)
def _clear_provider():
    """Local snapshot — module-level autouse in tests/conftest.py is added later."""
    saved = ruleset._provider
    ruleset._provider = None
    yield
    ruleset._provider = saved


class _StubProvider:
    name = "stub"

    # Methods are not exercised here — Protocol is structural.
    def init_sheet(self, npc_data): ...
    def update_hp(self, sheet, delta): ...
    def update_xp(self, sheet, delta): ...
    def set_field(self, sheet, field, value): ...
    def format_npc_sheet(self, npc_data): ...
    def format_party_summary(self, party): ...
    def format_character_block(self, character): ...
    def format_party_context_block(self, party, full): ...
    def xp_threshold(self, level): ...
    def level_for_xp(self, xp): ...
    def validate_skill(self, s): ...
    def validate_alignment(self, a): ...
    def validate_condition(self, c): ...
    def validate_damage_type(self, d): ...


def test_get_without_register_raises_runtime_error():
    with pytest.raises(RuntimeError, match="No ruleset registered"):
        ruleset.get()


def test_is_registered_reflects_state():
    assert ruleset.is_registered() is False
    ruleset.register(_StubProvider())
    assert ruleset.is_registered() is True


def test_register_then_get_returns_provider():
    p = _StubProvider()
    ruleset.register(p)
    assert ruleset.get() is p


def test_re_register_replaces_provider():
    p1 = _StubProvider()
    p2 = _StubProvider()
    ruleset.register(p1)
    ruleset.register(p2)
    assert ruleset.get() is p2
