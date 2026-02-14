# DM System Tests

## Structure

```
tests/
├── conftest.py              # Shared fixtures (temp campaigns)
├── test_encounter.py        # ✅ Encounter system (16 tests, all pass)
├── test_time_effects.py     # ✅ Time effects (11 tests, all pass)
└── README.md                # This file
```

## Running Tests

```bash
# All tests
uv run pytest tests/ -v

# Specific file
uv run pytest tests/test_encounter.py -v

# With coverage (if pytest-cov installed)
uv run pytest tests/ --cov=lib --cov-report=html
```

## Status

| Test File | Tests | Passing | Issues |
|-----------|-------|---------|--------|
| test_encounter.py | 16 | ✅ 16/16 | None |
| test_time_effects.py | 11 | ✅ 11/11 | None |

## Test Coverage

### Encounter System (`test_encounter.py`)

**Basic Tests:**
- System enabled/disabled detection
- Custom stat modifier calculation (e.g., awareness)
- Skill modifier usage (e.g., Perception)
- Ability modifier usage (e.g., DEX)

**DC Calculation:**
- Base DC without modifiers
- Distance-based DC increases
- Time-of-day modifiers (Night = +4 DC)
- DC cap at 30

**Segmentation:**
- Short distance (<1km) = 1 segment
- Medium distance (1-3km) = 1 segment
- Long distance (3-6km) = 2 segments
- Very long distance (6+km) = 3 segments

**Minimum Distance:**
- Journeys <300m are skipped
- Journeys >=300m are processed

**Encounter Nature:**
- Nature roll returns valid category
- Category ranges work correctly

### Time Effects (`test_time_effects.py`)

**Custom Stats:**
- Custom stats load correctly
- Stats have proper structure (current/max)

**Time Effects:**
- Time effects system enabled/disabled
- Hunger decreases over time (-2/hour)
- Thirst decreases faster than hunger (-3/hour)
- Radiation decays naturally (-1/hour)
- Stats clamp at minimum (0)
- Stats clamp at maximum (100)

**Precise Time:**
- Time format validation (HH:MM)
- Time advances correctly
- Time wraps after midnight

## Fixtures

### `minimal_campaign`
Basic campaign with minimal configuration for general testing.

### `stalker_campaign`
STALKER-themed campaign with:
- Custom stats (hunger, thirst, radiation, awareness)
- Time effects enabled
- Encounter system configured
- Coordinate-based locations (Cordon, Junkyard)

### `temp_campaign`
Minimal encounter-focused campaign for testing encounter mechanics.

## Example Test Patterns

### Regression Test
```python
def test_encounter_dc_balance_2024_02():
    """
    Ensure encounter DC balance hasn't changed.

    After code changes, verify that encounter probability
    for typical journeys remains within expected ranges.
    """
    enc = EncounterManager(...)

    # 2km during day should be ~40% chance
    dc = enc.calculate_dc(2.0, "Day")
    modifier = 0  # Average character
    success_rate = (20 - (dc - modifier)) / 20

    assert 0.35 <= success_rate <= 0.45, f"DC changed: {dc}"
```

### Parametrized Tests
```python
@pytest.mark.parametrize("distance,expected_segments", [
    (500, 1),
    (2000, 1),
    (4500, 2),
    (7000, 3),
])
def test_segmentation_table(distance, expected_segments):
    """Verify segmentation lookup table"""
    enc = EncounterManager(...)
    segments = enc.calculate_segments(distance)
    assert segments == expected_segments
```

## Best Practices

### 1. Use Fixtures for Setup
```python
@pytest.fixture
def character_with_high_awareness():
    return {"custom_stats": {"awareness": {"current": 80}}}
```

### 2. Test Edge Cases
```python
def test_dc_never_exceeds_30():
    """DC cap at 30 even for huge distances"""
    ...
```

### 3. Test Backward Compatibility
```python
def test_old_campaigns_without_awareness_still_work():
    """Campaigns without awareness shouldn't crash the system"""
    ...
```

### 4. Use Marks for Categories
```python
@pytest.mark.slow
def test_full_journey_with_encounters():
    """Slow integration test"""
    ...

# Run: pytest -m "not slow"
```

## CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install uv
      - run: uv pip install -r requirements.txt
      - run: uv run pytest tests/ -v --cov=lib
```

## Why pytest?

### Benefits for This Project

1. **Complex System** — Many interdependencies, easy to break
2. **JSON State** — Perfect for testing with fixtures
3. **Game Balance** — Need to track regressions
4. **Many Edge Cases** — Coordinates, time, stats
5. **Fast Feedback** — 27 tests run in ~0.1 seconds

### Future Enhancements

1. Property-based testing (hypothesis)
2. Snapshot testing for JSON (pytest-snapshot)
3. Performance benchmarks (pytest-benchmark)
4. Integration tests for full journeys
5. Coordinate system edge cases

## Roadmap

### Phase 1: Core Mechanics ✅
- [x] Encounter DC calculation
- [x] Stat modifiers (custom/skill/ability)
- [x] Segmentation logic
- [x] Distance filtering
- [x] Time effects on custom stats

### Phase 2: Integration (Next)
- [ ] Full journey with multiple encounters
- [ ] Waypoint creation/cleanup
- [ ] Stat-based consequence triggers
- [ ] Coordinate wrapping (359° + 5° = 4°)
- [ ] Path intersections

### Phase 3: Balance
- [ ] XP progression curves
- [ ] Encounter probability distribution
- [ ] Time effects rate balancing
- [ ] DC vs level scaling

### Phase 4: Advanced
- [ ] Session manager integration
- [ ] NPC interaction tests
- [ ] Combat system tests
- [ ] Quest progression tests

## Conclusion

**pytest is essential for this project:**

- ✅ Easy to write tests
- ✅ Fixtures for setup
- ✅ Fast execution
- ✅ CI/CD integration
- ✅ Finds bugs early

**Next Steps:**
1. Add session manager tests
2. Add coordinate system edge case tests
3. Set up CI/CD on GitHub
4. Add property-based testing
