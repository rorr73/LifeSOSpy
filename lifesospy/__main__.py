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
    client.on_connection_made = _on_connection_made
    client.on_response = _on_response
    loop.run_until_complete(_async_run_client_and_wait(client, loop))
    loop.close()

async def _async_run_client_and_wait(client, loop):
    await client.async_open()
    print("Press [Enter] to exit...\n")
    await loop.run_in_executor(None, sys.stdin.readline)
    client.close()

def _on_connection_made(client):
    asyncio.ensure_future(_async_test_commands(client), loop=client.event_loop)

async def _async_test_commands(client):
    _LOGGER.debug("Running test commands...")

    # Get the ROM Version from base unit
    response = await client.async_execute(GetROMVersionCommand())

    # Get/Set the current date/time from base unit
    response = await client.async_execute(GetDateTimeCommand())
    #response = await client.async_execute(SetDateTimeCommand())

    # Clear the alarm/warning LEDs on base unit and stop siren
    #response = await client.async_execute(ClearStatusCommand())

    # Get the current operation mode
    response = await client.async_execute(GetOpModeCommand())

    # Get/Set the exit delay
    response = await client.async_execute(GetExitDelayCommand())
    #response = await client.async_execute(SetExitDelayCommand(15))

    # Get/Set the entry delay
    response = await client.async_execute(GetEntryDelayCommand())
    #response = await client.async_execute(SetEntryDelayCommand(15))

    # Get the switches
    #for switch_number in SwitchNumber:
    #    response = await client.async_execute(GetSwitchCommand(switch_number))

    # Iterate through all device categories and get device info
    for dc in DC_ALL:
        if dc.max_devices:
            for index in range(0, dc.max_devices):
                response = await client.async_execute(GetDeviceByIndexCommand(dc, index))
                if isinstance(response, DeviceNotFoundResponse):
                    break

    _LOGGER.debug("Completed test commands.")

def _on_response(client, response, command):
    # To test running other clients (eg. HyperSecureLink) at same time
    if command is None:
        _LOGGER.debug("Response unsolicited: %s", response)

if __name__ == "__main__":
    main(sys.argv)
