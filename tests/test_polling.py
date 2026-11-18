"""A poll that overlaps a write must not put back a value read before the write (the display race of 0.1.1).

The fake ebusd answers from a dict standing for the bus; a hook runs a write (telegram, read-back stored as
coordinator.async_write stores it) between two commands of the poll, as the shared ebusd client allows."""
import asyncio

from weishaupt_core.polling import ReadBackStamps, poll
from weishaupt_core.registers import DEVICES, polls_programs, program_registers, registers_of

KA = next(d for d in DEVICES if d.key == "ka")
FS2 = next(d for d in DEVICES if d.key == "fs2")
GRADIENT = "0e01"  # a register of the FS (heating curve gradient)
assert GRADIENT in registers_of(FS2)
OLD, NEW = bytes.fromhex("c300"), bytes.fromhex("c800")  # 19.5 and 20.0


class Coordinator:
    """What the coordinator does around the poll: its data, and the write's read-back stored with a stamp."""

    def __init__(self, client):
        self.client = client
        self.data = None
        self.stamps = ReadBackStamps()

    async def refresh(self, read_programs=False):
        self.data = await poll(self.client, DEVICES, lambda: self.data, self.stamps, read_programs)

    async def write(self, device, register, raw):
        await self.client.write(device.zz, register, raw)
        after = (await self.client.read_registers(device.zz, [register]))[register]
        if self.data is not None:
            self.stamps.store(self.data, device.key, register, after)


class FakeEbusd:
    def __init__(self):
        self.bus = {d.zz: {r: bytes.fromhex("0100") for r in registers_of(d) + program_registers()} for d in DEVICES}
        self.bus[FS2.zz][GRADIENT] = OLD
        self.after_read = {}  # zz -> coroutine factory run right after the poll's read of that device
        self.reads = []
        self.lock = asyncio.Lock()

    async def read_registers(self, zz, registers):
        async with self.lock:
            await asyncio.sleep(0)
            values = {r: self.bus[zz][r] for r in registers}
        self.reads.append((zz, tuple(registers)))
        hook = self.after_read.pop(zz, None)
        if hook is not None:
            await hook()
        return values

    async def write(self, zz, register, raw):
        async with self.lock:
            self.bus[zz][register] = raw


def test_write_after_its_device_was_polled_keeps_the_read_back():
    """The case seen on the bus: the poll read the gradient (19.5), the restore to 20.0 was written and read back,
    then the poll ended. 0.1.1 showed 19.5 until the next poll; the read-back must stay."""
    client = FakeEbusd()
    coordinator = Coordinator(client)
    asyncio.run(coordinator.refresh())
    assert coordinator.data["fs2"][GRADIENT] == OLD

    async def scenario():
        client.after_read[FS2.zz] = lambda: coordinator.write(FS2, GRADIENT, NEW)
        await coordinator.refresh()
    asyncio.run(scenario())
    assert client.bus[FS2.zz][GRADIENT] == NEW
    assert coordinator.data["fs2"][GRADIENT] == NEW


def test_write_running_concurrently_with_the_poll():
    """Same, with the write as a separate task (the entity's service call) racing the poll on the shared client."""
    client = FakeEbusd()
    coordinator = Coordinator(client)
    asyncio.run(coordinator.refresh())

    async def scenario():
        started = asyncio.Event()

        async def hook():
            started.set()
        client.after_read[FS2.zz] = hook
        poll_task = asyncio.create_task(coordinator.refresh())
        await started.wait()
        await coordinator.write(FS2, GRADIENT, NEW)
        await poll_task
    asyncio.run(scenario())
    assert coordinator.data["fs2"][GRADIENT] == NEW


def test_write_before_its_device_is_polled_keeps_the_poll_value():
    """A read-back stored before the device is read is older than the poll's read: the poll's value wins (here the
    device changed again after the write, as a user at the panel could)."""
    client = FakeEbusd()
    coordinator = Coordinator(client)
    asyncio.run(coordinator.refresh())
    later = bytes.fromhex("cd00")

    async def change_at_the_panel():
        client.bus[FS2.zz][GRADIENT] = later

    async def scenario():
        async def hook():
            await coordinator.write(FS2, GRADIENT, NEW)  # before fs2 is read (ka is read first)
            client.after_read[FS2.zz] = change_at_the_panel
        client.after_read[KA.zz] = hook
        await coordinator.refresh()
    asyncio.run(scenario())
    assert coordinator.data["fs2"][GRADIENT] == NEW  # the poll read fs2 after the write: same value as the read-back
    asyncio.run(coordinator.refresh())
    assert coordinator.data["fs2"][GRADIENT] == later  # and the next poll is not held back by the old read-back


def test_program_register_copied_by_the_poll_keeps_the_read_back():
    """Programs are read once an hour; other polls copy them from the data. A program slot written during such a
    poll must not be put back to the copy."""
    client = FakeEbusd()
    coordinator = Coordinator(client)
    asyncio.run(coordinator.refresh(read_programs=True))
    slot = program_registers()[0]
    new_slot = bytes.fromhex("1a48")

    async def scenario():
        client.after_read[FS2.zz] = lambda: coordinator.write(FS2, slot, new_slot)
        await coordinator.refresh(read_programs=False)
    asyncio.run(scenario())
    assert coordinator.data["fs2"][slot] == new_slot


def test_read_back_differing_from_the_telegram_is_kept_as_read():
    """The read-back is stored as read (a value not retained shows what the device has), never the value sent."""
    client = FakeEbusd()
    coordinator = Coordinator(client)
    asyncio.run(coordinator.refresh())

    async def refused_write():
        client.bus[FS2.zz][GRADIENT] = OLD  # the device kept its value
    async def scenario():
        async def hook():
            await client.write(FS2.zz, GRADIENT, NEW)
            await refused_write()
            after = (await client.read_registers(FS2.zz, [GRADIENT]))[GRADIENT]
            coordinator.stamps.store(coordinator.data, "fs2", GRADIENT, after)
        client.after_read[FS2.zz] = hook
        await coordinator.refresh()
    asyncio.run(scenario())
    assert coordinator.data["fs2"][GRADIENT] == OLD


def test_poll_without_writes_is_unchanged():
    """Same reads, same order, same result as the poll of 0.1.1."""
    client = FakeEbusd()
    coordinator = Coordinator(client)
    asyncio.run(coordinator.refresh(read_programs=True))
    expected = []
    for device in DEVICES:
        expected.append((device.zz, tuple(registers_of(device))))
        if polls_programs(device):
            expected.append((device.zz, tuple(program_registers())))
    assert client.reads == expected
    for device in DEVICES:
        wanted = {r: client.bus[device.zz][r] for r in registers_of(device)}
        if polls_programs(device):
            wanted.update({r: client.bus[device.zz][r] for r in program_registers()})
        assert coordinator.data[device.key] == wanted
    client.reads.clear()
    asyncio.run(coordinator.refresh(read_programs=False))
    assert client.reads == [(d.zz, tuple(registers_of(d))) for d in DEVICES]
    assert coordinator.data["ka"][program_registers()[0]] == bytes.fromhex("0100")  # kept from the previous poll


def test_first_poll_without_data():
    stamps = ReadBackStamps()
    data = asyncio.run(poll(FakeEbusd(), DEVICES, lambda: None, stamps, True))
    assert set(data) == {d.key for d in DEVICES}


def test_stamps_order():
    stamps = ReadBackStamps()
    data = {"fs2": {GRADIENT: OLD}}
    before = stamps.now()
    stamps.store(data, "fs2", GRADIENT, NEW)
    after = stamps.now()
    assert data["fs2"][GRADIENT] == NEW
    polled = {"fs2": {GRADIENT: OLD}}
    assert stamps.keep_newer({"fs2": dict(polled["fs2"])}, data, {"fs2": before})["fs2"][GRADIENT] == NEW
    assert stamps.keep_newer({"fs2": dict(polled["fs2"])}, data, {"fs2": after})["fs2"][GRADIENT] == OLD
