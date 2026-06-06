"""Tests for json-wrappers-session: --json envelope over session read + write.

The CLI resolves the active campaign, so we test the enveloping hermetically: the
data methods (get_status read, move_party write) wrapped through emit() produce a
valid {"ok","data"} envelope. Live CLI --json is smoke-checked in the ticket QA.
"""

import contextlib
import io
import json

from lib.cli_output import emit
from lib.session_manager import SessionManager


def _envelope(data):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        emit(data, json_mode=True)
    return json.loads(buf.getvalue())


def test_status_read_envelopes(dcc_world):
    status = SessionManager(dcc_world).get_status()
    assert isinstance(status, dict)
    env = _envelope(status)
    assert env["ok"] is True and isinstance(env["data"], dict)


def test_move_write_envelopes(dcc_world):
    result = SessionManager(dcc_world).move_party("Test Alcove")
    assert isinstance(result, dict)
    env = _envelope(result)
    assert env["ok"] is True
