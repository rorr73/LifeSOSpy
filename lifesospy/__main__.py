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
    client.on_connected = on_connected
    client.on_response = on_response
    client.open()
    loop.run_until_complete(prompt_and_wait(loop))
    client.close()
    loop.close()

def on_response(client, response, command):
    pass

def on_connected(client):
    asyncio.ensure_future(test_commands(client), loop=client.event_loop)

async def test_commands(client):
    # Get the ROM Version from base unit
    response = await client.execute(GetROMVersionCommand())

    # Get the current operation mode
    response = await client.execute(GetOpModeCommand())

    # Iterate through all device categories and get device info
    for dc in DC_ALL.values():
        for index in range(0, dc.max_devices):
            response = await client.execute(GetDeviceByIndexCommand(dc, index))
            if isinstance(response, DeviceNotFoundResponse):
                break

async def prompt_and_wait(loop):
    print("Press [Enter] to exit...\n")
    await loop.run_in_executor(None, sys.stdin.readline)

if __name__ == "__main__":
    main(sys.argv)
