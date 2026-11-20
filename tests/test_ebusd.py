"""The ebusd client and its parsers, against the recorded answers of a real ebusd."""
import pytest

from weishaupt_core.ebusd import (
    CommandRefused,
    EbusdClient,
    EbusdConnectionError,
    EbusdNoData,
    EbusdNoSignal,
    EbusdNotFound,
    check_command,
    check_read_only,
    parse_definitions,
    parse_info,
)


def test_parse_info(golden):
    info = parse_info(golden["info"])
    assert info.version.startswith("26.1")
    assert info.signal is False  # recorded without a bus
    boiler = info.slave("08")
    assert (boiler.manufacturer, boiler.ident, boiler.software) == ("Kromschroeder", "W", "1104")
    assert boiler.files == ("kromschroeder/08.w.bc1.csv",)
    assert info.slave("36") is None  # ebusd's own slave address
    assert info.slave("10") is None  # a master
    scanned = sorted(a.address for a in info.addresses.values() if a.scanned)
    assert scanned == ["08", "15", "18", "35", "50", "51", "52", "75", "f5"]


def test_parse_info_of_a_running_ebusd():
    info = parse_info('version: ebusd 26.1.abc\nsignal: acquired\naddress 31: master #8, ebusd\n'
                      'address 15: slave #2, scanned "MF=X;ID=Y;SW=0102;HW=0304", loaded "a.csv", "b.csv"\n')
    assert info.signal and info.addresses["31"].own
    assert info.slave("15").files == ("a.csv", "b.csv")


def test_parse_definitions(golden):
    definitions = {d.name: d for d in parse_definitions(golden["definitions"]["bc1"])}
    assert len(definitions) == 28
    counters = definitions["Counters"]
    assert counters.is_read and not counters.is_passive
    assert [(f.name, f.type, f.unit) for f in counters.fields] == [
        ("firstbyte", "UCH", ""), ("operatinghours", "U3N", "h"), ("burnerhours", "UIN", "h"),
        ("burnerstarts", "U3N", "")]
    status = {d.name: d for d in parse_definitions(golden["definitions"]["ka"])}["Boiler1Status"]
    assert status.is_passive and status.fields[2].type == "BI0:1"
    assert status.fields[1].divisor_or_values.startswith("0=BurnerOff;1=StandbyCheckFan")
    assert parse_definitions("ERR: element not found") == []


@pytest.mark.parametrize("command", [
    "write -c ka BlockingTime 2", "write -s ff -c ka BlockingTime 2", "hex 15502303", "scan full", "grab",
    "reload", "define -r x", "read -h 15502203ccb001", "read -s ff -c ka BlockingTime", "read -def r,,x", ""])
def test_only_reading_commands_pass(command):
    with pytest.raises(CommandRefused):
        check_read_only(command)


@pytest.mark.parametrize("command", ["info", "find -f -c ka", "read -m 300 -c ka BlockingTime"])
def test_reading_commands_pass(command):
    check_read_only(command)


@pytest.mark.parametrize("command", [
    "write -s ff -c ka -h 155023052825000100", "write -c em2 -h 51502305fe2800f302",
    "write -c weishaupt-probe -h 155023052825000100"])
def test_the_register_write_passes(command):
    check_command(command)


@pytest.mark.parametrize("command", [
    "write -s ff -c ka BlockingTime 2",  # by name: ebusd would compute the checksum, or not
    "write -c ka BlockingTime 2",
    "write -s 10 -c ka -h 155023052825000100",  # another source address
    "write -s ff -h 155023052825000100",  # no circuit: ebusd would not check it
    "write -s ff -c ka -h 15502306282500010000",  # another length
    "write -s ff -c ka -h 155022032825 00",  # a read
    "write -s ff -c ka -h 155023052825000100 x",
    "write -def w,ka,X,,,15,5023,2500,,,UIN 1",
    "write -s ff -c ka -h fe5023052825000100".replace("fe", "f e"),
    "hex -s ff 155023052825000100", "inject ff155023052825000100/00", "answer x"])
def test_every_other_write_is_refused(command):
    with pytest.raises(CommandRefused):
        check_command(command)


async def test_client_against_the_simulated_ebusd(fake):
    client = EbusdClient("127.0.0.1", fake.port)
    info = await client.info()
    assert info.signal and info.slave("15") is not None
    assert len(await client.definitions("ka")) == 50
    assert await client.definitions("nothing") == []
    assert await client.read("bc1", "Temperatures", 300) == ("0", "60", "52", "63", "15")
    assert await client.read("ka", "Boiler1Power", 900) == ("54", "23", "100")
    with pytest.raises(EbusdNotFound):
        await client.read("ka", "NoSuchMessage", 300)
    fake.reads.pop("ka/Boiler1Power")
    with pytest.raises(EbusdNoData):
        await client.read("ka", "Boiler1Power", 900)
    fake.signal = False
    with pytest.raises(EbusdNoSignal):
        await client.read("bc1", "Temperatures", 300)
    assert client.requests == {"find": 2, "info": 1, "read": 5, "write": 0}


async def test_a_refused_command_is_never_sent(fake):
    client = EbusdClient("127.0.0.1", fake.port)
    with pytest.raises(CommandRefused):
        await client._command("write -s ff -c ka BlockingTime 2")
    assert fake.commands == []


async def test_unreachable(socket_enabled):
    with pytest.raises(EbusdConnectionError):
        await EbusdClient("127.0.0.1", 1, timeout=2).info()
