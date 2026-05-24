"""Bootstrap default ruleset.

Side-effecting import. Order matters: `lib.ruleset` must be imported first so
that `register` is defined before `rulesets.dnd_5e.__init__` tries to call it.
Importing `rulesets.dnd_5e` first would resolve `from lib.ruleset import register`
against a still-partial `lib` module and fail.
"""
import sys
from pathlib import Path

# Defensive: ensure project root is on sys.path so `rulesets` resolves even under
# non-uv Python invocations (e.g. `python3 lib/foo.py`). Idempotent.
_root = Path(__file__).parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from lib import ruleset  # noqa: F401  — `register` must be defined first
import rulesets.dnd_5e   # noqa: F401  — side-effect: registers DnD5eRuleset
