import argparse
import asyncio
import logging
import sys

from lifesospy.client import Client
from lifesospy.command import *
from lifesospy.const import *
from lifesospy.response import *

_LOGGER = logging.getLogger(__name__)

def main(argv):
    """Simple runnable command line script to test library."""

    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser(
        description="LifeSOSpy: Provides connectivity to a LifeSOS alarm system.")
    parser.add_argument(
        '-H', '--host',
        help="Hostname/IP Address for the LifeSOS ethernet interface.",
        required=True)
    parser.add_argument(
        '-P', '--port',
        help="TCP port for the LifeSOS ethernet interface.",
        default='1680')
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    client = Client(args.host, args.port, loop)
    client.on_connected = _on_connected
    client.on_response = _on_response
    client.open()
    loop.run_until_complete(_prompt_and_wait(loop))
    client.close()
    loop.close()

def _on_connected(client):
    asyncio.ensure_future(_test_commands(client), loop=client.event_loop)

async def _test_commands(client):
    _LOGGER.debug("Running test commands...")

    # Get the ROM Version from base unit
    response = await client.execute(GetROMVersionCommand())

    # Get the current date/time from base unit
    response = await client.execute(GetDateTimeCommand())

    # Set the current date/time on base unit
    #response = await client.execute(SetDateTimeCommand())

    # Clear the alarm/warning LEDs on base unit and stop siren
    #response = await client.execute(ClearStatusCommand())

    # Get the current operation mode
    response = await client.execute(GetOpModeCommand())

    # Iterate through all device categories and get device info
    for dc in DC_ALL:
        if dc.max_devices:
            for index in range(0, dc.max_devices):
                response = await client.execute(GetDeviceByIndexCommand(dc, index))
                if isinstance(response, DeviceNotFoundResponse):
                    break

    _LOGGER.debug("Completed test commands.")

def _on_response(client, response, command):
    # To test running other clients (eg. HyperSecureLink) at same time
    if command is None:
        _LOGGER.debug("Response unsolicited: %s", response)

async def _prompt_and_wait(loop):
    print("Press [Enter] to exit...\n")
    await loop.run_in_executor(None, sys.stdin.readline)

if __name__ == "__main__":
    main(sys.argv)
