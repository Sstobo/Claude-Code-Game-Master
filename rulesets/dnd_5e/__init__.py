"""Side-effecting import: registers DnD5eRuleset with lib.ruleset on import."""
from lib.ruleset import register
from .provider import DnD5eRuleset

register(DnD5eRuleset())
