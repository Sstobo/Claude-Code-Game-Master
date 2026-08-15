#!/usr/bin/env python3
"""
Generic, system-agnostic game core.

NO D&D 5e assumptions live here: no fixed ability names, no level-20 cap, no spell
slots. The core provides only the universal primitives every world runs on:

  - resolution:  resolve_check (the kit's resolution model) + opposed_check (contest)
  - harm:        apply_harm / heal on an abstract HP value
  - conditions:  add_condition / remove_condition on a list
  - progression: three interchangeable models (milestone / resource-axis / xp-levels)

Stat names, combat feel, signature systems, and the choice of progression model are
BESPOKE PER WORLD (a World Kit configures them). dice.py is the only RNG.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from dice import DiceRoller

_roller = DiceRoller()

_ADV_NOTATION = {'advantage': '2d20kh1', 'disadvantage': '2d20kl1', None: '1d20'}
_2D6_NOTATION = {'advantage': '3d6kh2', 'disadvantage': '3d6kl2', None: '2d6'}

DEFAULT_RESOLUTION_MODEL = 'd20-vs-dc'


def _warn(message: str) -> None:
    """Visible one-line warning on stderr — never stdout, which carries --json."""
    print(f"[WARNING] {message}", file=sys.stderr)


def _split_model(model: Any) -> tuple:
    """(name, params) from either 'd20-vs-dc' or {'model': ..., 'params': {...}}."""
    if isinstance(model, dict):
        params = {k: v for k, v in model.items() if k != 'model'}
        params.update(params.pop('params', {}) or {})
        return (model.get('model') or DEFAULT_RESOLUTION_MODEL), params
    return (model or DEFAULT_RESOLUTION_MODEL), {}


# ---------------------------------------------------------------- resolution

def resolve_check(modifier: int = 0, dc: int = 10, advantage: Optional[str] = None,
                  model: Any = None) -> Dict[str, Any]:
    """Resolve a check under the active World Kit's RESOLUTION MODEL.

    modifier/dc/advantage are model-agnostic; `model` is the kit's declared model
    (a name, or the {model, params} shape WorldKit.resolution() returns). Omitted
    -> 'd20-vs-dc', so every existing caller keeps d20 behavior unchanged.

    Models:
      d20-vs-dc      1d20 + mod vs DC. crit 'hit' on a natural 20, 'miss' on a 1.
      2d6-plus-mod   2d6 + mod vs DC. crit 'hit' on 12, 'miss' on 2.
      dice-pool      N d6 (N = modifier, min 1) counting `target`+ (default 5) as
                     successes; DC is the successes REQUIRED. crit 'hit' when
                     every die succeeds, 'miss' on zero successes.

    Every model returns the same keys: die, modifier, total, dc, success, margin,
    critical. For the pool, `die` is the success count and `modifier` the pool size.
    An unrecognized model warns on stderr (per call) and falls back to d20.
    """
    name, params = _split_model(model)
    if name == '2d6-plus-mod':
        return _resolve_2d6(modifier, dc, advantage)
    if name == 'dice-pool':
        return _resolve_pool(modifier, dc, advantage, int(params.get('target', 5)))
    if name != DEFAULT_RESOLUTION_MODEL:
        _warn(f"unknown resolution model '{name}' — falling back to {DEFAULT_RESOLUTION_MODEL}")
    return _resolve_d20(modifier, dc, advantage)


def _result(die: int, modifier: int, total: int, dc: int, critical: Optional[str]) -> Dict[str, Any]:
    return {
        'die': die,
        'modifier': modifier,
        'total': total,
        'dc': dc,
        'success': total >= dc,
        'margin': total - dc,
        'critical': critical,
    }


def _resolve_d20(modifier: int, dc: int, advantage: Optional[str]) -> Dict[str, Any]:
    r = _roller.roll(_ADV_NOTATION.get(advantage, '1d20'))
    kept = r.get('kept', r.get('rolls', []))
    die = kept[0] if kept else r['total']
    return _result(die, modifier, r['total'] + modifier, dc,
                   'hit' if die == 20 else 'miss' if die == 1 else None)


def _resolve_2d6(modifier: int, dc: int, advantage: Optional[str]) -> Dict[str, Any]:
    """PbtA-flavored 2d6 + mod. Advantage rolls 3d6 and keeps the best two."""
    r = _roller.roll(_2D6_NOTATION.get(advantage, '2d6'))
    kept = r.get('kept', r.get('rolls', []))
    die = sum(kept) if kept else r['total']
    return _result(die, modifier, die + modifier, dc,
                   'hit' if die == 12 else 'miss' if die == 2 else None)


def _resolve_pool(modifier: int, dc: int, advantage: Optional[str], target: int) -> Dict[str, Any]:
    """Success-counting pool: the modifier IS the dice pool, the DC is successes needed."""
    pool = max(1, modifier + (1 if advantage == 'advantage' else -1 if advantage == 'disadvantage' else 0))
    rolls = _roller.roll(f"{pool}d6")['rolls']
    successes = sum(1 for face in rolls if face >= target)
    critical = 'hit' if successes == pool else 'miss' if successes == 0 else None
    return _result(successes, pool, successes, dc, critical)


def opposed_check(modifier_a: int = 0, modifier_b: int = 0,
                  advantage_a: Optional[str] = None, advantage_b: Optional[str] = None,
                  model: Any = None) -> Dict[str, Any]:
    """Resolve an opposed contest between A and B under the kit's resolution model.

    Both sides roll the SAME model and are compared on that model's own axis: totals
    for d20 and 2d6, success COUNTS for a pool (where `total` is the count). There is
    no DC in a contest — the sides are ranked against each other — so each side is
    resolved at DC 0 and only its axis value is read. Ties go to neither.
    """
    a = resolve_check(modifier_a, 0, advantage_a, model=model)
    b = resolve_check(modifier_b, 0, advantage_b, model=model)
    if a['total'] > b['total']:
        winner = 'a'
    elif b['total'] > a['total']:
        winner = 'b'
    else:
        winner = 'tie'
    return {'a': a['total'], 'b': b['total'], 'winner': winner, 'margin': abs(a['total'] - b['total'])}


# ---------------------------------------------------------------- harm / conditions

def apply_harm(current_hp: int, amount: int) -> int:
    """Reduce HP by amount, floored at 0."""
    return max(0, current_hp - max(0, amount))


def classify_harm(current_hp: int, max_hp: int, amount: int,
                  lethality: Dict[str, Any] = None) -> Dict[str, Any]:
    """Apply harm and classify the outcome under the kit's lethality model.

    Returns ``{new_hp, outcome}`` with outcome ``'ok' | 'dying' | 'dead'``. The
    default ``death-saves`` model matches 5e: dropping to 0 opens the *dying*
    gate, and only massive overkill (damage past 0 >= max HP) or an explicit
    lower ``massive_damage_at`` kills outright. A grittier kit sets model
    ``'gritty'`` — 0 HP is *dead*, no saves — and any kit can lower
    ``massive_damage_at`` to make single hits lethal sooner. Model ``'none'``
    never instant-kills (pure damage floor).

    This is a pure calculator; persistence + the death-save ceremony are the
    caller's (gm-combat / the Death Protocol) job.
    """
    lethality = lethality or {}
    model = lethality.get("model", "death-saves")
    amount = max(0, amount)
    new_hp = max(0, current_hp - amount)
    overkill = max(0, amount - current_hp)  # damage dealt past 0
    threshold = lethality.get("massive_damage_at", max_hp)
    if model != "none" and overkill >= threshold:
        return {"new_hp": 0, "outcome": "dead"}
    if new_hp == 0:
        return {"new_hp": 0, "outcome": "dead" if model == "gritty" else "dying"}
    return {"new_hp": new_hp, "outcome": "ok"}


def heal(current_hp: int, max_hp: int, amount: int) -> int:
    """Increase HP by amount, capped at max_hp."""
    return min(max_hp, current_hp + max(0, amount))


def add_condition(conditions: List[str], condition: str) -> List[str]:
    """Add a condition (idempotent). Returns a new list."""
    out = list(conditions or [])
    if condition and condition not in out:
        out.append(condition)
    return out


def remove_condition(conditions: List[str], condition: str) -> List[str]:
    """Remove a condition if present. Returns a new list."""
    return [c for c in (conditions or []) if c != condition]


# ---------------------------------------------------------------- progression

class Progression:
    """Interface: advance(state, **kw) -> state; level(state) -> int."""

    name = 'base'

    def advance(self, state: Dict[str, Any], **kw) -> Dict[str, Any]:
        raise NotImplementedError

    def level(self, state: Dict[str, Any]) -> int:
        raise NotImplementedError


class MilestoneProgression(Progression):
    """Story-beat advancement. No XP math; the GM grants milestones."""

    name = 'milestone'

    def advance(self, state, **kw):
        state = dict(state or {})
        state['milestone'] = int(state.get('milestone', 0)) + int(kw.get('count', 1))
        return state

    def level(self, state):
        return int((state or {}).get('milestone', 0))


class XpLevelProgression(Progression):
    """XP-threshold leveling. Thresholds are SUPPLIED (not a hardcoded 5e table)."""

    name = 'xp-levels'

    def __init__(self, thresholds: List[int] = None):
        # thresholds[i] = XP required to reach level i+2 (level 1 starts at 0 xp).
        self.thresholds = list(thresholds or [])

    def advance(self, state, **kw):
        state = dict(state or {})
        state['xp'] = int(state.get('xp', 0)) + int(kw.get('xp', 0))
        state['level'] = self.level(state)
        return state

    def level(self, state):
        xp = int((state or {}).get('xp', 0))
        lvl = 1
        for t in self.thresholds:
            if xp >= t:
                lvl += 1
            else:
                break
        return lvl


class ResourceAxisProgression(Progression):
    """Progression along a world resource/clock (DCC viewers, Dune spice, ...).

    `tiers` are SUPPLIED resource thresholds; level = number of tiers reached.
    """

    name = 'resource-axis'

    def __init__(self, resource: str = 'resource', tiers: List[int] = None):
        self.resource = resource
        self.tiers = list(tiers or [])

    def advance(self, state, **kw):
        state = dict(state or {})
        state[self.resource] = int(state.get(self.resource, 0)) + int(kw.get('amount', 0))
        return state

    def level(self, state):
        value = int((state or {}).get(self.resource, 0))
        return sum(1 for t in self.tiers if value >= t)


# ----------------------------------------------- discretionary "spectacle" award
#
# A kit-agnostic reward path for MEANINGFUL RESOLUTION of any kind — not just
# kills. A clever skill check, a social victory, an exploration breakthrough, a
# daring escape, or surviving punishing odds can all grant progress through the
# SAME door. Combat's CR->XP table is just one source of XP among many; this is
# the others.
#
# This is a PURE calculator: it turns a tier + the character's progress context
# into the amounts to apply. The caller (player_manager) persists the result and
# runs level-up detection, so this stays file-system- and kit-shape-agnostic.

# Sane defaults a kit overrides via ruleset.json -> progression.spectacle.tiers.
# XP is scaled to the gap to the next level so a beat stays meaningful at any
# level/floor; `xp_floor` guarantees a minimum. `followers` is only applied when
# the kit declares a secondary `follower_field` (e.g. DCC viewers).
DEFAULT_SPECTACLE_TIERS = {
    'minor':     {'xp_frac': 0.20, 'xp_floor': 50,  'followers': 250,  'milestone': 0},
    'major':     {'xp_frac': 0.50, 'xp_floor': 150, 'followers': 1500, 'milestone': 0},
    'legendary': {'xp_frac': 1.00, 'xp_floor': 400, 'followers': 8000, 'milestone': 1},
}


def spectacle_award(tier: str,
                    progression_model: str = 'milestone',
                    xp_to_next: int = 0,
                    tiers: Dict[str, Any] = None,
                    has_follower_currency: bool = False) -> Dict[str, Any]:
    """Compute a discretionary spectacle reward, kit-agnostically.

    tier                 'minor' | 'major' | 'legendary' (or any kit-defined key).
    progression_model    the active kit's model: 'xp-levels' / 'level' grant XP;
                         'milestone' grants milestone count; 'resource-axis' is
                         driven by its resource (followers) when present.
    xp_to_next           XP remaining to the next level (used to scale XP rewards).
    tiers                kit tier table (ruleset override), else DEFAULT_SPECTACLE_TIERS.
    has_follower_currency  True if the kit declares a follower/viewer field to co-award.

    Returns {'ok', 'tier', 'xp', 'followers', 'milestone'} — amounts to apply.
    Unknown tier -> {'ok': False, 'error': ...}.
    """
    table = tiers or DEFAULT_SPECTACLE_TIERS
    key = (tier or '').lower()
    if key not in table:
        return {'ok': False, 'error': f"unknown tier '{tier}'", 'valid': list(table.keys())}
    spec = table[key]

    xp = 0
    milestone = 0
    # XP-based kits ('xp-levels' and the 'level' alias) get scaled XP.
    if progression_model in ('xp-levels', 'level'):
        gap = max(0, int(xp_to_next))
        xp = max(int(spec.get('xp_floor', 0)), int(round(gap * float(spec.get('xp_frac', 0)))))
    elif progression_model == 'milestone':
        # No XP math — a legendary beat can be worth a milestone tick.
        milestone = int(spec.get('milestone', 0))

    followers = int(spec.get('followers', 0)) if has_follower_currency else 0

    return {'ok': True, 'tier': key, 'xp': xp, 'followers': followers, 'milestone': milestone}


# ------------------------------------------- signature-system primitives
#
# Four world-agnostic building blocks a World Kit instantiates and NAMES per
# world — a corruption meter, a Warp price, a morale reaction, a cursed-hoard
# payoff. Like `spectacle_award`, each is a PURE CALCULATOR: it reads no files
# and writes none, takes all its content (names, thresholds, dice) as arguments,
# and returns a plain dict for the caller to persist. Nothing here is book-
# specific; the kit supplies the flavor. Rolls are seedable via `rng` (any object
# with `randint(a, b)`, e.g. random.Random(seed)) so tests are deterministic;
# without one they reuse the module dice roller.


def _roll_total(notation: str, rng: Any = None) -> int:
    """Total of a simple 'NdM' roll. `rng` (e.g. random.Random) makes it
    deterministic; without one, reuse the module DiceRoller (global RNG).

    Config dice here are bare 'NdM' (1d20, 2d6); the modifier travels separately.
    """
    if rng is None:
        return _roller.roll(notation)['total']
    count_s, _, sides_s = (notation or '').strip().lower().partition('d')
    count, sides = int(count_s or 1), int(sides_s)
    return sum(rng.randint(1, sides) for _ in range(count))


def _rung_for(rungs: List[Dict[str, Any]], value: int, key: str) -> Optional[Dict[str, Any]]:
    """Pick the rung with the greatest `key` still ≤ value; below all, the lowest."""
    ordered = sorted(rungs or [], key=lambda r: r[key])
    chosen = ordered[0] if ordered else None
    for r in ordered:
        if value >= r[key]:
            chosen = r
        else:
            break
    return chosen


def named_track(current: int, delta: int, config: Dict[str, Any]) -> Dict[str, Any]:
    """A meter with threshold consequences (corruption, doom, heat, ...).

    config = {"max": int, "thresholds": [{"at": int, "consequence": str}, ...]}.
    Applies delta, clamping the result to [0, max]. Deterministic (no roll).

    Returns {"before", "after", "max", "crossed", "at_max"} where `crossed` is the
    threshold dicts this delta newly passed through in EITHER direction (before <
    at ≤ after climbing, or after < at ≤ before falling), sorted by `at`.
    """
    max_v = int(config.get('max', 0))
    before = int(current)
    after = max(0, min(max_v, before + int(delta)))
    lo, hi = min(before, after), max(before, after)
    crossed = [t for t in (config.get('thresholds') or [])
               if lo < int(t['at']) <= hi]
    crossed.sort(key=lambda t: int(t['at']))
    return {'before': before, 'after': after, 'max': max_v,
            'crossed': crossed, 'at_max': after >= max_v}


def price_roll(severity: int, config: Dict[str, Any], rng: Any = None) -> Dict[str, Any]:
    """The cost a marked action exacts from the actor (a Warp roll, a debt, a scar).

    config = {"ladder": [{"min_roll": int, "cost": str}, ...], "dice": "1d20",
    "modifier": int}. Rolls dice + modifier − severity (higher severity => a lower
    total => a WORSE rung), then reads the ladder rung whose `min_roll` the total
    reaches (below the cheapest rung, it lands on the worst one).

    Returns {"roll", "total", "severity", "cost", "rung"} (rung is the chosen dict).
    """
    roll = _roll_total(config.get('dice', '1d20'), rng)
    total = roll + int(config.get('modifier', 0)) - int(severity)
    rung = _rung_for(config.get('ladder') or [], total, 'min_roll')
    return {'roll': roll, 'total': total, 'severity': int(severity),
            'cost': (rung or {}).get('cost'), 'rung': rung}


def reaction_roll(track_value: int, config: Dict[str, Any], rng: Any = None) -> Dict[str, Any]:
    """An NPC's opening disposition, shifted by a track/reputation value.

    config = {"dice": "2d6", "tiers": [{"min": int, "reaction": str}, ...],
    "modifier": int}. Rolls dice + modifier + track_value and maps the total to the
    tier whose `min` it reaches (below the lowest tier, it lands on the worst one).

    Returns {"roll", "total", "track_value", "reaction", "tier"} (tier is the dict).
    """
    roll = _roll_total(config.get('dice', '2d6'), rng)
    total = roll + int(config.get('modifier', 0)) + int(track_value)
    tier = _rung_for(config.get('tiers') or [], total, 'min')
    return {'roll': roll, 'total': total, 'track_value': int(track_value),
            'reaction': (tier or {}).get('reaction'), 'tier': tier}


def guarded_payoff(config: Dict[str, Any], rng: Any = None) -> Dict[str, Any]:
    """Rolled BEFORE a marked treasure is taken — does the hoard bite back?

    config = {"dice": "1d20", "clean_at": int, "guardian_at": int} with
    clean_at > guardian_at. High roll walks away clean; a middling roll wakes the
    guardian; a low roll attaches the curse.

    Returns {"roll", "outcome"} where outcome is
    "clean" | "guardian_wakes" | "curse_attaches".
    """
    roll = _roll_total(config.get('dice', '1d20'), rng)
    if roll >= int(config.get('clean_at', 0)):
        outcome = 'clean'
    elif roll >= int(config.get('guardian_at', 0)):
        outcome = 'guardian_wakes'
    else:
        outcome = 'curse_attaches'
    return {'roll': roll, 'outcome': outcome}


def make_progression(model: str, **config) -> Progression:
    """Factory: build a progression model by name.

    'level' is a documented alias for 'xp-levels' (spectacle_award honors it too).

    Unknown -> milestone, but VISIBLY: a typo in ruleset.json ('xp-level' for
    'xp-levels') used to cost a campaign its XP math with no signal anywhere, so an
    unrecognized name warns on stderr. An absent model is the declared default and
    stays silent.
    """
    if model in ('xp-levels', 'level'):
        return XpLevelProgression(thresholds=config.get('thresholds'))
    if model == 'resource-axis':
        return ResourceAxisProgression(resource=config.get('resource', 'resource'),
                                       tiers=config.get('tiers'))
    if model and model != 'milestone':
        _warn(f"unknown progression model '{model}' — falling back to milestone")
    return MilestoneProgression()


# ------------------------------------------------------------ self-check
#
# `uv run python lib/game_core.py` exercises the signature-system primitives at
# their edges and fails loudly (AssertionError) if a contract breaks. `_Fixed`
# is a loaded die (its face clamps into range) so best/worst rolls are exact
# without depending on a seed's luck; random.Random proves seedable determinism.

class _Fixed:
    """A loaded die: rng.randint(a, b) always returns `face`, clamped to [a, b]."""

    def __init__(self, face: int):
        self.face = face

    def randint(self, a: int, b: int) -> int:
        return min(max(self.face, a), b)


def _demo() -> None:
    # named_track — empty track: no movement, nothing crossed.
    cfg_t = {'max': 100, 'thresholds': [{'at': 50, 'consequence': 'corrupted'},
                                        {'at': 100, 'consequence': 'lost'}]}
    empty = named_track(0, 0, cfg_t)
    assert empty == {'before': 0, 'after': 0, 'max': 100, 'crossed': [], 'at_max': False}, empty

    # delta past max clamps and reports at_max, crossing both thresholds upward.
    up = named_track(40, 90, cfg_t)
    assert up['after'] == 100 and up['at_max'] is True, up
    assert [t['at'] for t in up['crossed']] == [50, 100], up

    # downward delta crosses on the way back down; clamps at 0.
    down = named_track(60, -80, cfg_t)
    assert down['after'] == 0 and down['at_max'] is False, down
    assert [t['at'] for t in down['crossed']] == [50], down

    # price_roll — worst and best rung, deterministic via loaded die.
    cfg_p = {'dice': '1d20', 'modifier': 0,
             'ladder': [{'min_roll': 0, 'cost': 'a piece of your soul'},
                        {'min_roll': 10, 'cost': 'a lasting scar'},
                        {'min_roll': 18, 'cost': 'nothing but a nosebleed'}]}
    worst = price_roll(severity=5, config=cfg_p, rng=_Fixed(1))   # 1 - 5 = -4 -> bottom rung
    assert worst['cost'] == 'a piece of your soul' and worst['total'] == -4, worst
    best = price_roll(severity=0, config=cfg_p, rng=_Fixed(20))   # 20 -> top rung
    assert best['cost'] == 'nothing but a nosebleed' and best['rung']['min_roll'] == 18, best

    # reaction_roll — both extremes (hostile floor, allied ceiling).
    cfg_r = {'dice': '2d6', 'modifier': 0,
             'tiers': [{'min': -99, 'reaction': 'hostile'},
                       {'min': 7, 'reaction': 'neutral'},
                       {'min': 12, 'reaction': 'helpful'}]}
    hostile = reaction_roll(track_value=-10, config=cfg_r, rng=_Fixed(1))   # 2 - 10 = -8
    assert hostile['reaction'] == 'hostile', hostile
    helpful = reaction_roll(track_value=5, config=cfg_r, rng=_Fixed(6))     # 12 + 5 = 17
    assert helpful['reaction'] == 'helpful' and helpful['total'] == 17, helpful

    # guarded_payoff — each of the three outcomes.
    cfg_g = {'dice': '1d20', 'clean_at': 15, 'guardian_at': 8}
    assert guarded_payoff(cfg_g, rng=_Fixed(20))['outcome'] == 'clean'
    assert guarded_payoff(cfg_g, rng=_Fixed(10))['outcome'] == 'guardian_wakes'
    assert guarded_payoff(cfg_g, rng=_Fixed(1))['outcome'] == 'curse_attaches'

    # seedable determinism: the same seed reproduces the same roll.
    import random
    a = price_roll(2, cfg_p, rng=random.Random(1234))
    b = price_roll(2, cfg_p, rng=random.Random(1234))
    assert a == b, (a, b)

    print('[game_core] signature-system primitives self-check OK')


if __name__ == '__main__':
    _demo()
