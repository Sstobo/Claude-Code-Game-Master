"""Phase 5: validators treat sheet shape as opaque."""
from lib import schemas


def test_validate_npc_accepts_arbitrary_character_sheet():
    """Lib shouldn't reject sheets just because hp isn't a {current, max} dict.

    The active ruleset re-validates on action paths (init_sheet / update_hp /
    set_field). Lib stays opaque.
    """
    data = {
        'description': 'd', 'attitude': 'friendly',
        'is_party_member': True,
        'character_sheet': {'hp': 25, 'mojo': 7},  # not 5E-shaped
    }
    valid, errors = schemas.validate_npc('Carl', data)
    assert valid, f"expected valid, got errors: {errors}"


def test_validate_npc_rejects_non_dict_character_sheet():
    data = {
        'description': 'd', 'attitude': 'friendly',
        'is_party_member': True, 'character_sheet': "not a dict",
    }
    valid, errors = schemas.validate_npc('Carl', data)
    assert not valid


def test_validate_character_accepts_flat_arbitrary_fields():
    char = {
        'name': 'Stalker', 'race': 'human', 'class': 'mercenary', 'level': 1,
        'hp': 25,  # not a dict
        'custom_stats': {'radiation': 0},
    }
    valid, errors = schemas.validate_character(char)
    assert valid, f"expected valid, got errors: {errors}"


def test_validate_character_requires_core_lib_fields():
    valid, errors = schemas.validate_character({})
    assert not valid
    joined = " ".join(errors)
    for field in ('name', 'race', 'class', 'level'):
        assert field in joined
