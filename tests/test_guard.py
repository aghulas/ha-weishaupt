import pytest

from weishaupt_core.guard import (
    LOG_FRESH_MAX,
    MAX_PER_HOUR,
    ServiceToolState,
    WriteGuard,
    WriteRefused,
    read_service_tool_state,
)


class Clock:
    def __init__(self, t=1_000_000.0):
        self.t = t

    def __call__(self):
        return self.t


def guard(enabled=True):
    clock = Clock()
    return WriteGuard(enabled, clock=clock), clock


def test_disabled_refuses_everything():
    g, _ = guard(enabled=False)
    with pytest.raises(WriteRefused):
        g.check("fs1:0500", 21, 10, 26, None)


def test_bounds():
    g, _ = guard()
    with pytest.raises(WriteRefused):
        g.check("fs1:0500", 27, 10, 26, None)
    g.check("fs1:0500", 26, 10, 26, None)


def test_rate_limits():
    g, clock = guard()
    g.check("fs1:0500", 21, 10, 26, None)
    g.record("fs1:0500", None)
    with pytest.raises(WriteRefused):
        g.check("fs1:0500", 21.5, 10, 26, None)
    clock.t += 11
    g.check("fs1:0500", 21.5, 10, 26, None)
    for i in range(MAX_PER_HOUR - 1):
        g.record(f"r{i}", None)
    with pytest.raises(WriteRefused):
        g.check("fs2:0500", 21, 10, 26, None)
    clock.t += 3601
    g.check("fs2:0500", 21, 10, 26, None)


def test_ff_needs_a_readable_log():
    g, clock = guard()
    with pytest.raises(WriteRefused):
        g.check("fs1:0500", 21, 10, 26, "ff")
    with pytest.raises(WriteRefused):
        g.check("fs1:0500", 21, 10, 26, "ff", ServiceToolState(error="no such file"))
    g.check("fs1:0500", 21, 10, 26, "ff", ServiceToolState(None, newest=clock.t))


def test_ff_refused_when_log_stale():
    g, clock = guard()
    with pytest.raises(WriteRefused):  # newest telegram too old: the add-on stopped logging, detector is blind
        g.check("fs1:0500", 21, 10, 26, "ff", ServiceToolState(None, newest=clock.t - LOG_FRESH_MAX - 10))
    g.check("fs1:0500", 21, 10, 26, "ff", ServiceToolState(None, newest=clock.t))  # fresh log, no recent ff


def test_ff_refused_while_service_tool_active():
    g, clock = guard()
    with pytest.raises(WriteRefused):
        g.check("fs1:0500", 21, 10, 26, "ff", ServiceToolState(clock.t - 60, newest=clock.t))
    g.check("fs1:0500", 21, 10, 26, "ff", ServiceToolState(clock.t - 601, newest=clock.t))
    g.check("fs1:0500", 21, 10, 26, None, ServiceToolState(clock.t - 60))  # 31 is not concerned


def test_own_ff_writes_do_not_block():
    g, clock = guard()
    g.record("fs1:0500", "ff")
    own = clock.t
    clock.t += 30
    g.check("fs1:0800", 14, 5, 20, "ff", ServiceToolState(own + 1, newest=clock.t))


def test_nan_is_out_of_bounds():
    g, _ = guard()
    with pytest.raises(WriteRefused) as err:
        g.check("fs1:0500", float("nan"), 10, 26, None)
    assert err.value.code == "out_of_bounds"


def test_unreadable_log_file(tmp_path):
    state = read_service_tool_state(str(tmp_path / "missing.db"))
    assert state.error is not None
    g, _ = guard()
    with pytest.raises(WriteRefused) as err:
        g.check("15:2500", 2, 0, 30, "ff", state)
    assert err.value.code == "log_unreadable"
