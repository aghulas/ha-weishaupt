import pytest

from weishaupt_core.guard import MAX_PER_HOUR, ServiceToolState, WriteGuard, WriteRefused


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
    g, _ = guard()
    with pytest.raises(WriteRefused):
        g.check("fs1:0500", 21, 10, 26, "ff")
    with pytest.raises(WriteRefused):
        g.check("fs1:0500", 21, 10, 26, "ff", ServiceToolState(error="no such file"))
    g.check("fs1:0500", 21, 10, 26, "ff", ServiceToolState(None))


def test_ff_refused_while_service_tool_active():
    g, clock = guard()
    with pytest.raises(WriteRefused):
        g.check("fs1:0500", 21, 10, 26, "ff", ServiceToolState(clock.t - 60))
    g.check("fs1:0500", 21, 10, 26, "ff", ServiceToolState(clock.t - 601))
    g.check("fs1:0500", 21, 10, 26, None, ServiceToolState(clock.t - 60))  # 31 is not concerned


def test_own_ff_writes_do_not_block():
    g, clock = guard()
    g.record("fs1:0500", "ff")
    own = clock.t
    clock.t += 30
    g.check("fs1:0800", 14, 5, 20, "ff", ServiceToolState(own + 1))


def test_broadcast_guard_disabled():
    g, _ = guard(enabled=False)
    with pytest.raises(WriteRefused):
        g.check_broadcast()


def test_broadcast_guard_rate_and_interval():
    g, clock = guard()
    g.check_broadcast()
    g.record_broadcast()
    with pytest.raises(WriteRefused):  # less than MIN_INTERVAL since the last clock broadcast
        g.check_broadcast()
    clock.t += 11
    g.check_broadcast()
    g.record_broadcast()
    for i in range(MAX_PER_HOUR):
        g.record(f"r{i}", None)
    clock.t += 11
    with pytest.raises(WriteRefused):  # hourly cap shared with register writes
        g.check_broadcast()
