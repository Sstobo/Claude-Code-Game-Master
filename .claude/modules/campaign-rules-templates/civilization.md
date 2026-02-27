## id
civilization

## name
Civilization / Tribe

## description
Managing a civilization from tribe to empire. Population, technologies, resources, and faith drive every decision. Each turn is an era.

## genres
strategy, civilization, 4X, tribal, empire-building, historical

## recommended_for
Campaigns where the player governs a people, not a character. Development from hunter-gatherers to modernity. Multiple players as faction leaders.

## rules

### Time Scale

A turn = as much time as needed for meaningful progress. DM chooses the scale based on context:

| Situation | Turn scale |
|-----------|-----------|
| Active crisis (war, epidemic, famine) | days — weeks |
| Construction, research, diplomacy | months — a season |
| Peaceful development, population growth | a year — several years |
| Era transition, major time skip | decades |

**Principle:** local events don't drag on. If an NPC disappeared or a village is burning — that's not grounds for weeks of detective work. The DM summarizes the outcome in one turn and moves on. Details only matter if they change the civilization globally.

**Each turn the DM announces:** how much time passed and what changed (population, resources, neighbors, events). The Ruler reacts to the big picture, not every minor detail.

### Eras and Progress

Campaign eras: **Stone Age → Bronze → Iron → Medieval → Renaissance → Industrial → Modern**.

- Era transition: DM decides when the civilization is "ready" — based on accumulated technologies, buildings, population
- Each era unlocks new buildings, units, technologies
- Regression is real: catastrophic population loss can push the civilization back an era

### Food and Consumption

**Food drain:**
```
Food_per_hour = Population × food_coefficient
```

`food_coefficient` — starting value **0.5**, DM adjusts it during play:
- Each food technology (Agriculture, Irrigation, etc.) reduces the coefficient
- Famine, drought, disease — raise it
- DM announces coefficient changes and their cause

**Food shortage consequences:**
- Stock drops to 25%: Famine — Morale -1/session, population growth halted
- Stock drops to 0: Plague — Population -1d10 each session until food is restored

### Technologies

Technologies are stored in inventory as items: `[Tech: Pottery]`, `[Tech: Writing]`.

**Research**
Each technology has a **progress bar 0–100%**. The civilization researches it gradually.

**Research roll** — once per session if there is an active research:
```
d20 + Era_bonus vs DC
```

**DC by era:**
| Technology belongs to... | Base DC |
|--------------------------|---------|
| Current era | 14 |
| Previous era | 10 |
| Two eras back | 6 |

**Era_bonus** — grows as the civilization advances, DM assigns (+0 Stone Age, +2 Bronze, +4 Iron, etc.)

**Roll results:**
- Failure (below DC): +5–10% progress — the civilization learns even from mistakes
- Success (DC met): +25–40% progress
- Nat 20: +50% or immediate discovery at DM's discretion
- At 100% — technology unlocked, bonus activates

**Research resources** — DM assigns based on the technology and era. Examples: Pottery requires clay and time by the fire; Metallurgy requires ore and smiths; Writing requires free people (not everyone hunting).

### Buildings

DM assigns cost and construction time based on era and available resources. Guidelines:
- Simple structure (pit, shelter): 1–3 days, basic materials
- Medium (huts, palisade): a week, wood + labor
- Complex (temple, walls): a month+, rare materials

### Culture and Faith

**Culture Points** (CP) and **Faith Points** (FP) accumulate from civilization actions, not just buildings.

CP grows from: rituals, trade, establishing traditions, cultural decisions of the Ruler.
FP grows from: sacrifices, shaman rituals, religious events.

**Culture thresholds:**
- 10 CP: +1 to negotiations with neighbors
- 25 CP: Cultural influence — neighboring tribe DC 14 Wisdom or adopts your customs
- 50 CP: Cultural victory without war (DC 18 Diplomacy)

**Faith thresholds:**
- 10 FP: +1 to rolls against disease and anomalies
- 20 FP: Shaman can heal 1/day (DC 12)
- 40 FP: Holy war — Military +3, Morale cannot drop below 5

### Military

- Army = share of population in military role × technology bonus
- Attack: d20 + Military_score vs DC (10 + enemy Military_score / 2)
- Victory: enemy loses 20% Population and some resources
- Defeat: own army -30%, Morale -3

### Diplomacy and Trade

- Trade route: both sides +resources/session, requires mutual agreement
- Alliance: +2 to joint actions, obligation to aid under attack
- Espionage: DC 15 → steal a technology or sabotage production for a season

### Natural Events (d20 once per season)

| Roll | Event |
|------|-------|
| 1–2 | Catastrophe — random building destroyed, -2d10 Population |
| 3–5 | Disease — DC 13 or -1d8 Population × 3 turns |
| 6–8 | Drought — food_coefficient ×1.5 for a season |
| 9–12 | Normal |
| 13–16 | Good harvest — food_coefficient ×0.7 for a season |
| 17–19 | Discovery — new resource or +20% progress on a random technology |
| 20 | Golden Age — all production +25%, Morale +5 for a season |

### Advisors

The Ruler is immortal and impassive — they observe and direct. Advisors are the voice of the civilization.

**Advisor roles** are defined by the civilization's current needs. No need — no advisor.

Example roles:
- **Military** — army, defense, raids
- **Spiritual** — faith, rituals, morale
- **Resources** — food, construction, economy
- **Diplomat** — neighbors, trade, alliances
- **Science** — research, technologies
- **Trade** — economy, routes, taxation

DM introduces and removes advisors during play. If religion is banned — the Spiritual advisor leaves. No neighbors — no Diplomat needed. Isolated civilization — a Survival advisor appears.

Advisors are faceless — they have no names, personalities, or personal agendas. They are functions, not characters. Generations pass, faces change — the role remains.

Advisors **propose** actions and **report** results. The DM rolls dice on behalf of the civilization — the Ruler rolls nothing.

### Loss Conditions

- **Population → 0**: civilization extinct. Game over.
- **Population < 10**: civilization absorbed by neighbors or scattered. Game over unless there is a rescue plan within 1 session.
- **All advisors abandon the Ruler**: anarchy. DM gives 1 session to restore order, otherwise game over.
