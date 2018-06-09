from abc import ABC, abstractmethod
from datetime import datetime
from lifesospy.const import *
from lifesospy.util import *

class Command(ABC):
    """Represents a command to be issued to the LifeSOS base unit."""

    @property
    @abstractmethod
    def name(self):
        """Provides the command name."""
        return ''

    @property
    def action(self):
        """When implemented, provides the action to perform; eg. get, set."""
        return ''

    @property
    def args(self):
        """When implemented, provides arguments for the command."""
        return ''

    def format(self, password=''):
        """Format command along with any arguments, ready to be sent."""
        return MARKER_START + \
            self.name + \
            self.action + \
            self.args + \
            password + \
            MARKER_END

class NoOpCommand(Command):
    """Command that does nothing."""

    @property
    def name(self):
        return ''

class GetDateTimeCommand(Command):
    """Command to get the date/time from the LifeSOS base unit."""

    @property
    def name(self):
        return CMD_DATETIME

    @property
    def action(self):
        return ACTION_GET

class SetDateTimeCommand(Command):
    """Command to set the date/time on the LifeSOS base unit."""

    def __init__(self, value=None):
        """If value is not specified, the current local date/time will be used."""
        self._value = value

    @property
    def name(self):
        return CMD_DATETIME

    @property
    def action(self):
        return ACTION_SET

    @property
    def args(self):
        value = self._value
        if not value:
            value = datetime.now()
        return value.strftime('%y%m%d%w%H%M')

class GetOpModeCommand(Command):
    """Command to get the current operation mode from the LifeSOS base unit."""

    @property
    def name(self):
        return CMD_OPMODE

    @property
    def action(self):
        return ACTION_GET

class SetOpModeCommand(Command):
    """Command to set the operation mode on the LifeSOS base unit."""

    def __init__(self, operation_mode):
        self._operation_mode = operation_mode

    @property
    def name(self):
        return CMD_OPMODE

    @property
    def action(self):
        return ACTION_SET

    @property
    def args(self):
        return str(int(self._operation_mode))

class GetDeviceByIndexCommand(Command):
    """Get a device (by index) for specified category from the LifeSOS base unit."""

    def __init__(self, device_category, index):
        self._device_category = device_category
        self._index = index

    @property
    def name(self):
        return CMD_DEVBYIDX_PREFIX + self._device_category.id

    @property
    def action(self):
        return ACTION_GET

    @property
    def args(self):
        return to_ascii_hex(self._index, 2)

class GetDeviceByZoneCommand(Command):
    """Get a device (by zone) for specified category from the LifeSOS base unit."""

    def __init__(self, device_category, group_number, unit_number):
        self._device_category = device_category
        self._group_number = group_number
        self._unit_number = unit_number

    @property
    def name(self):
        return CMD_DEVBYZON_PREFIX + self._device_category.id

    @property
    def action(self):
        return ACTION_GET

    @property
    def args(self):
        return '{0:02x}{1:02x}'.format(self._group_number, self._unit_number)

class ClearStatusCommand(Command):
    """Clear the alarm/warning LEDs on base unit and stop siren."""

    @property
    def name(self):
        return CMD_CLEAR_STATUS

class GetROMVersionCommand(Command):
    """Command to get the ROM version string from the LifeSOS base unit."""

    @property
    def name(self):
        return CMD_ROMVER

    @property
    def action(self):
        return ACTION_GET

class GetExitDelayCommand(Command):
    """Command to get the exit delay from the LifeSOS base unit."""

    @property
    def name(self):
        return CMD_EXIT_DELAY

    @property
    def action(self):
        return ACTION_GET

class SetExitDelayCommand(Command):
    """Command to set the exit delay on the LifeSOS base unit."""

    def __init__(self, exit_delay):
        if exit_delay < 0x00:
            raise ValueError("Exit delay cannot be negative.")
        elif exit_delay > 0xff:
            raise ValueError("Exit delay cannot exceed %s seconds.", 0xff)
        self._exit_delay = exit_delay

    @property
    def name(self):
        return CMD_EXIT_DELAY

    @property
    def action(self):
        return ACTION_SET

    @property
    def args(self):
        return to_ascii_hex(self._exit_delay, 2)

class GetEntryDelayCommand(Command):
    """Command to get the entry delay from the LifeSOS base unit."""

    @property
    def name(self):
        return CMD_ENTRY_DELAY

    @property
    def action(self):
        return ACTION_GET

class SetEntryDelayCommand(Command):
    """Command to set the entry delay on the LifeSOS base unit."""

    def __init__(self, entry_delay):
        if entry_delay < 0x00:
            raise ValueError("Entry delay cannot be negative.")
        elif entry_delay > 0xff:
            raise ValueError("Entry delay cannot exceed %s seconds.", 0xff)
        self._entry_delay = entry_delay

    @property
    def name(self):
        return CMD_ENTRY_DELAY

    @property
    def action(self):
        return ACTION_SET

    @property
    def args(self):
        return to_ascii_hex(self._entry_delay, 2)

class GetSwitchCommand(Command):
    """Command to get the state of a switch."""

    def __init__(self, switch_number):
        self._switch_number = switch_number

    @property
    def name(self):
        return CMD_SWITCH_PREFIX + to_ascii_hex(self._switch_number.value, 1)

    @property
    def action(self):
        return ACTION_GET

class SetSwitchCommand(Command):
    """Command to set the state of a switch."""

    def __init__(self, switch_number, switch_state):
        self._switch_number = switch_number
        self._switch_state = switch_state

    @property
    def name(self):
        return CMD_SWITCH_PREFIX + to_ascii_hex(self._switch_number.value, 1)

    @property
    def action(self):
        return ACTION_SET

    @property
    def args(self):
        return to_ascii_hex(self._switch_state, 1)
