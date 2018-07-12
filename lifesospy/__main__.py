"""
This module allows the library to be run as an interactive command line
application, primarily to assist with testing the library.
"""

import argparse
import asyncio
import logging
import sys
import traceback

from typing import Optional, Union
from lifesospy.baseunit import BaseUnit
from lifesospy.const import (
    PROJECT_VERSION, PROJECT_DESCRIPTION)
from lifesospy.devicecategory import DeviceCategory, DC_ALL_LOOKUP
from lifesospy.enums import (
    OperationMode, ESFlags, SSFlags, SwitchFlags, SwitchNumber)

_LOGGER = logging.getLogger(__name__)


def main(argv):
    """
    Basic command line script for testing library.
    """

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="LifeSOSpy v{} - {}".format(
            PROJECT_VERSION, PROJECT_DESCRIPTION))
    parser.add_argument(
        '-H', '--host',
        help="Hostname/IP Address for the LifeSOS server, if we are to run as a client.",
        default=None)
    parser.add_argument(
        '-P', '--port',
        help="TCP port for the LifeSOS ethernet interface.",
        default=str(BaseUnit.TCP_PORT))
    parser.add_argument(
        '-p', '--password',
        help="Password for the Master user, if remote access requires it.",
        default='')
    parser.add_argument(
        '-v', '--verbose',
        help="Display all logging output.",
        action='store_true')
    args = parser.parse_args()

    # Configure logger
    logging.basicConfig(
        format="%(asctime)s %(levelname)-5s (%(threadName)s) [%(name)s] %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG if args.verbose else logging.INFO)

    # Create base unit instance and start up interface
    print("LifeSOSpy v{} - {}\n".format(PROJECT_VERSION, PROJECT_DESCRIPTION))
    loop = asyncio.get_event_loop()
    baseunit = BaseUnit(args.host, args.port)
    if args.password:
        baseunit.password = args.password
    baseunit.start()

    # Provide interactive prompt for running test commands on another thread
    loop.run_until_complete(
        loop.run_in_executor(
            None, _handle_interactive_baseunit_tests, baseunit, loop))

    # Shut down interface and event loop
    baseunit.stop()
    loop.close()


def _handle_interactive_baseunit_tests(
        baseunit: BaseUnit, loop: asyncio.AbstractEventLoop) -> None:
    # pylint: disable=broad-except
    # pylint: disable=missing-docstring

    help_message = (
        "Test commands available:\n"
        "'exit' - exit this application\n"
        "'help' - display this list of available commands\n"
        "'devices' - list all discovered devices\n"
        "'disarm' - set Disarm mode\n"
        "'home' - set Home mode\n"
        "'away' - set Away mode\n"
        "'monitor' - set Monitor mode\n"
        "'clear' - clear status LEDs and stop siren\n"
        "'setdatetime' - set remote date/time to match local\n"
        "'sw##' - toggle switch; ## must be between 01 and 16\n"
        "'add X' - add new device for category X (one of c/b/f/m/e)\n"
        "'change ID G U ES SW' - change device settings, where ID is 6 char hex \n"
        "                        device id, G = group#, U = unit#, ES = enable \n"
        "                        status flags, SW = switch flags\n"
        "'changespecial ID G U ES SW SS HL LL (CH CL)' - same as change, plus\n"
        "                        SS = special status flags, HL/LL = high/low,\n"
        "                        CH/CL = control high/low (if supported)"
        "'delete ID' - delete device, where ID is 6 char hex device id\n"
        "'eventlog (#)' - get event log, optionally get only # most recent\n"
        "'sensorlog (#)' - get sensor log, optionally get only # most recent")
    print(help_message)

    while True:
        line = sys.stdin.readline().strip().lower()

        # Exit test app
        if line == 'exit':
            break

        # Display list of available commands and the arguments required
        elif line == 'help':
            print(help_message)

        # Print all enrolled devices
        elif line == 'devices':
            for device in baseunit.devices:
                print(device)

        # Set operation mode
        elif line in (str(op).lower() for op in OperationMode):
            async def async_set_operation_mode(operation_mode: OperationMode):
                try:
                    await baseunit.async_set_operation_mode(operation_mode)
                    print("Operation mode was set to {}.".format(str(operation_mode)))
                except Exception:
                    traceback.print_exc()

            operation_mode = next(op for op in OperationMode if str(op).lower() == line)
            asyncio.run_coroutine_threadsafe(
                async_set_operation_mode(operation_mode), loop)

        # Clear status
        elif line == 'clear':
            async def async_clear_status():
                try:
                    await baseunit.async_clear_status()
                    print("Cleared status on base unit.")
                except Exception:
                    traceback.print_exc()

            asyncio.run_coroutine_threadsafe(
                async_clear_status(), loop)

        # Set current date/time
        elif line == 'setdatetime':
            async def async_set_datetime():
                try:
                    await baseunit.async_set_datetime()
                    print("Base unit has been set to the current date/time.")
                except Exception:
                    traceback.print_exc()

            asyncio.run_coroutine_threadsafe(
                async_set_datetime(), loop)

        # Toggle specified switch
        # 'SW01' - toggle switch 1
        elif line.startswith('sw'):
            async def async_set_switch_state(switch_number: SwitchNumber, new_state: bool):
                try:
                    await baseunit.async_set_switch_state(switch_number, new_state)
                    print("Switch {} is now {}.".format(
                        str(switch_number), "on" if new_state else "off"))
                except Exception:
                    traceback.print_exc()

            switch_number = next((item for item in SwitchNumber if str(item) == line.upper()), None)
            if switch_number is None:
                print("Invalid switch number.")
                continue
            new_state = not baseunit.switch_state[switch_number]
            asyncio.run_coroutine_threadsafe(
                async_set_switch_state(switch_number, new_state), loop)

        # Add device to specified category
        # 'add b' - start listening for a new Burglar device to add
        # Note - only enables listening mode. The actual completion (or error)
        #        when done happens later via a second response.
        elif line.startswith('add '):
            async def async_add_device(device_category: DeviceCategory):
                try:
                    await baseunit.async_add_device(device_category)
                    print("Base unit now listening for new device.")
                except Exception:
                    traceback.print_exc()

            args = line.split()
            device_category = DC_ALL_LOOKUP.get(args[1])
            if device_category is None or device_category.max_devices is None:
                print("Invalid device category id.")
                continue
            asyncio.run_coroutine_threadsafe(
                async_add_device(device_category), loop)

        # Change settings for device on the base unit
        # 'change 123456 01 02 4410 0000' - change device 123456 to
        #  zone 01-02, enable status flags 4410 and switch flags 0000
        elif line.startswith('change '):
            async def async_change_device(
                    device_id: int, group_number: int, unit_number: int,
                    enable_status: ESFlags, switches: SwitchFlags):
                try:
                    await baseunit.async_change_device(
                        device_id, group_number, unit_number, enable_status,
                        switches)
                    print("Changed settings for device. New device settings:\n"
                          + str(baseunit.devices[device_id]))
                except Exception:
                    traceback.print_exc()

            args = line.split()
            try:
                device_id = int(args[1], 16)
            except Exception:
                print("Invalid device id.")
                continue
            try:
                group_number = int(args[2], 16)
                unit_number = int(args[3], 16)
                enable_status = ESFlags(int(args[4], 16))
                switches = SwitchFlags(int(args[5], 16))
            except Exception:
                print("Invalid args.")
                continue
            asyncio.run_coroutine_threadsafe(
                async_change_device(
                    device_id, group_number, unit_number, enable_status,
                    switches), loop)

        # Change settings for 'Special' device on the base unit
        # 'changespecial 123456 01 02 4410 0000 00 40 none 30 10' - change
        #  device 123456 to zone 01-02, enable status flags 4410,
        #  switch flags 0000, special status flags 00, alarm high 40 degrees,
        #  no alarm low, control high 30 degrees, control low 10 degrees.
        elif line.startswith('changespecial '):
            async def async_change_special_device(
                    device_id: int, group_number: int, unit_number: int,
                    enable_status: ESFlags, switches: SwitchFlags,
                    special_status: SSFlags,
                    high_limit: Optional[Union[int, float]],
                    low_limit: Optional[Union[int, float]],
                    control_high_limit: Optional[Union[int, float]],
                    control_low_limit: Optional[Union[int, float]]):
                try:
                    await baseunit.async_change_special_device(
                        device_id, group_number, unit_number, enable_status,
                        switches, special_status, high_limit, low_limit,
                        control_high_limit, control_low_limit)
                    print("Changed settings for device. New device settings:\n"
                          + str(baseunit.devices[device_id]))
                except Exception:
                    traceback.print_exc()

            args = line.split()
            try:
                device_id = int(args[1], 16)
            except Exception:
                print("Invalid device id.")
                continue
            try:
                group_number = int(args[2], 16)
                unit_number = int(args[3], 16)
                enable_status = ESFlags(int(args[4], 16))
                switches = SwitchFlags(int(args[5], 16))
                special_status = SSFlags(int(args[6], 16))
                high_limit = _parse_special_value(args[7])
                low_limit = _parse_special_value(args[8])
                control_high_limit = None \
                    if len(args) <= 9 else _parse_special_value(args[9])
                control_low_limit = None \
                    if len(args) <= 10 else _parse_special_value(args[10])
            except Exception:
                print("Invalid args.")
                continue
            asyncio.run_coroutine_threadsafe(
                async_change_special_device(
                    device_id, group_number, unit_number, enable_status,
                    switches, special_status, high_limit, low_limit,
                    control_high_limit, control_low_limit), loop)

        # Delete device with specified id
        # 'delete 123456' - delete device 123456
        elif line.startswith('delete '):
            async def async_delete_device(device_id: int):
                try:
                    device = baseunit.devices[device_id]
                    await baseunit.async_delete_device(device_id)
                    print("Deleted device:\n" + str(device))
                except Exception:
                    traceback.print_exc()

            args = line.split()
            try:
                device_id = int(args[1], 16)
            except Exception:
                print("Invalid device id.")
                continue
            asyncio.run_coroutine_threadsafe(
                async_delete_device(device_id), loop)

        # Get event log entries
        # 'eventlog' - get all entries
        # 'eventlog 50' - get only the 50 most recent entries
        elif line.startswith('eventlog'):
            async def async_get_event_log(baseunit: BaseUnit,
                                          max_count: Optional[int]) -> None:
                # Get first entry in memory, as we need the index of the last entry
                response = await baseunit.async_get_event_log(0)
                if response is None:
                    print("The event log is empty.")
                    return

                # Go backwards from the end (most recent entry) to the start (oldest)
                index = response.last_index
                if max_count is None:
                    first_index = 0
                else:
                    first_index = max(0, index + 1 - max_count)
                print("There are {} log entries; showing {}...".format(
                    index + 1,
                    "all" if max_count is None or first_index == 0 else
                    "{} most recent".format(max_count)))
                while index >= first_index:
                    response = await baseunit.async_get_event_log(index)
                    if response is not None:
                        print(response)
                    index -= 1

            args = line.split()
            max_count = None
            if len(args) > 1:
                try:
                    max_count = int(args[1])
                    if max_count < 1:
                        raise ValueError
                except Exception:
                    print("Max Count must be a positive number.")
                    continue
            asyncio.run_coroutine_threadsafe(
                async_get_event_log(baseunit, max_count), loop)

        # Get sensor log readings for 'Special' devices
        # 'sensorlog' - get all readings
        # 'sensorlog 50' - get only the 50 most recent readings
        elif line.startswith('sensorlog'):
            async def async_get_sensor_log(baseunit: BaseUnit,
                                           max_count: Optional[int]) -> None:
                # Get first entry in memory, as we need the index of the last entry
                response = await baseunit.async_get_sensor_log(0)
                if response is None:
                    print("The sensor log is empty.")
                    return

                # Go backwards from the end (most recent entry) to the start (oldest)
                index = response.last_index
                if max_count is None:
                    first_index = 0
                else:
                    first_index = max(0, index + 1 - max_count)
                print("There are {} readings; showing {}...".format(
                    index + 1,
                    "all" if max_count is None or first_index == 0 else
                    "{} most recent".format(max_count)))
                while index >= first_index:
                    response = await baseunit.async_get_sensor_log(index)
                    if response is not None:
                        print(response)
                    index -= 1

            args = line.split()
            max_count = None
            if len(args) > 1:
                try:
                    max_count = int(args[1])
                    if max_count < 1:
                        raise ValueError
                except Exception:
                    print("Max Count must be a positive number.")
                    continue
            asyncio.run_coroutine_threadsafe(
                async_get_sensor_log(baseunit, max_count), loop)


def _parse_special_value(text: str) -> Optional[Union[int, float]]:
    if text == 'none':
        return None
    try:
        return int(text)
    except ValueError:
        return float(text)


if __name__ == "__main__":
    main(sys.argv)
