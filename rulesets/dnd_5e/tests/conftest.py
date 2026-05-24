"""Subtree provider-snapshot fixture.

pytest runs the suite in one process, so side-effecting `import rulesets.dnd_5e`
leaves `lib.ruleset._provider` set globally. Snapshot/restore around each test.
"""
import pytest

from lib import ruleset


@pytest.fixture(autouse=True)
def _snapshot_provider():
    saved = ruleset._provider
    yield
    ruleset._provider = saved
