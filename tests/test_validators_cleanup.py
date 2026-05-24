"""Phase 2 cleanup — the four 5E vocab methods must be gone from lib.validators."""
from lib.validators import Validators


def test_dnd_vocab_methods_removed():
    v = Validators()
    for name in ("validate_skill", "validate_alignment",
                 "validate_condition", "validate_damage_type"):
        assert not hasattr(v, name), f"{name} should be removed from lib.validators"


def test_generic_validators_remain():
    v = Validators()
    for name in ("validate_name", "validate_attitude", "validate_dice",
                 "validate_ability", "validate_quest_priority",
                 "validate_time_of_day", "validate_plot_type",
                 "validate_plot_status"):
        assert hasattr(v, name), f"{name} should remain in lib.validators"
