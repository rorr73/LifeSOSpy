from abc import ABC, abstractmethod
from datetime import datetime
from lifesospy.const import *
from lifesospy.devicecategory import *
from lifesospy.enums import *
from lifesospy.util import *
from typing import Dict, Any, Optional


class Command(ABC):
    """Represents a command to be issued to the LifeSOS base unit."""

    @property
    def action(self) -> str:
        """When implemented, provides the action to perform; eg. get, set."""
        return ACTION_NONE

    @property
    def args(self) -> str:
        """When implemented, provides arguments for the command."""
        return ''

    @property
    @abstractmethod
    def name(self) -> str:
        """Provides the command name."""
        return ''

    def format(self, password: str = '') -> str:
        """Format command along with any arguments, ready to be sent."""
        return MARKER_START + \
            self.name + \
            self.action + \
            self.args + \
            password + \
            MARKER_END

    def __repr__(self) -> str:
        return "<{}: {}>".format(self.__class__.__name__,
                                   self.format())

    def as_dict(self) -> Dict[str, Any]:
        """Converts to a dict of attributes for easier JSON serialisation."""
        return obj_to_dict(self)


class NoOpCommand(Command):
    """Command that does nothing."""

    @property
    def name(self) -> str:
        """Provides the command name."""
        return ''


class GetDateTimeCommand(Command):
    """Command to get the date/time from the LifeSOS base unit."""

    @property
    def action(self) -> str:
        """Provides the action to perform."""
        return ACTION_GET

    @property
    def name(self) -> str:
        """Provides the command name."""
        return CMD_DATETIME


class SetDateTimeCommand(Command):
    """Command to set the date/time on the LifeSOS base unit."""

    def __init__(self, value: datetime = None):
        """If value is not specified, the current local date/time will be used."""
        self._value = value

    @property
    def action(self) -> str:
        """Provides the action to perform."""
        return ACTION_SET

    @property
    def args(self) -> str:
        """Provides arguments for the command."""
        value = self._value
        if not value:
            value = datetime.now()
        return value.strftime('%y%m%d%w%H%M')

    @property
    def name(self) -> str:
        """Provides the command name."""
        return CMD_DATETIME

    @property
    def value(self) -> Optional[datetime]:
        """Date/Time to be set, or None for the current local date/time."""
        return self._value


class GetOpModeCommand(Command):
    """Command to get the current operation mode from the LifeSOS base unit."""

    @property
    def action(self) -> str:
        """Provides the action to perform."""
        return ACTION_GET

    @property
    def name(self) -> str:
        """Provides the command name."""
        return CMD_OPMODE


class SetOpModeCommand(Command):
    """Command to set the operation mode on the LifeSOS base unit."""

    def __init__(self, operation_mode: OperationMode):
        self._operation_mode = operation_mode

    @property
    def action(self) -> str:
        """Provides the action to perform."""
        return ACTION_SET

    @property
    def args(self) -> str:
        """Provides arguments for the command."""
        return str(int(self._operation_mode))

    @property
    def name(self) -> str:
        """Provides the command name."""
        return CMD_OPMODE

    @property
    def operation_mode(self) -> OperationMode:
        """Operation mode to be set."""
        return self._operation_mode


class GetDeviceByIndexCommand(Command):
    """Get a device using the specified category and index."""

    def __init__(self, device_category: DeviceCategory, index: int):
        self._device_category = device_category
        self._index = index

    @property
    def action(self) -> str:
        """Provides the action to perform."""
        return ACTION_GET

    @property
    def args(self) -> str:
        """Provides arguments for the command."""
        return to_ascii_hex(self._index, 2)

    @property
    def device_category(self) -> DeviceCategory:
        """Category for the device."""
        return self._device_category

    @property
    def index(self) -> int:
        """Index of device within the category (also known as memory address)."""
        return self._index

    @property
    def name(self) -> str:
        """Provides the command name."""
        return CMD_DEVBYIDX_PREFIX + self._device_category.id


class GetDeviceCommand(Command):
    """Get a device using the specified category and zone."""

    def __init__(self, device_category: DeviceCategory, group_number: int, unit_number: int):
        self._device_category = device_category
        self._group_number = group_number
        self._unit_number = unit_number

    @property
    def action(self) -> str:
        """Provides the action to perform."""
        return ACTION_GET

    @property
    def args(self) -> str:
        """Provides arguments for the command."""
        return '{}{}'.format(
            to_ascii_hex(self._group_number, 2),
            to_ascii_hex(self._unit_number, 2))

    @property
    def device_category(self) -> DeviceCategory:
        """Category for the device."""
        return self._device_category

    @property
    def group_number(self) -> int:
        """Group number the device is assigned to."""
        return self._group_number

    @property
    def name(self) -> str:
        """Provides the command name."""
        return CMD_DEVICE_PREFIX + self._device_category.id

    @property
    def unit_number(self) -> int:
        """Unit number the device is assigned to (within group)."""
        return self._unit_number


class ChangeDeviceCommand(Command):
    """Change settings for a device on the base unit."""

    def __init__(self, device_category: DeviceCategory, index: int,
                 group_number: int, unit_number: int, enable_status: ESFlags,
                 switches: SwitchFlags):
        self._device_category = device_category
        self._index = index
        self._group_number = group_number
        self._unit_number = unit_number
        self._enable_status = enable_status
        self._switches = switches

    @property
    def action(self) -> str:
        """Provides the action to perform."""
        return ACTION_SET

    @property
    def args(self) -> str:
        """Provides arguments for the command."""
        return '{}{}{}{}{}'.format(
            to_ascii_hex(self._index, 2),
            to_ascii_hex(self._group_number, 2),
            to_ascii_hex(self._unit_number, 2),
            to_ascii_hex(int(self._enable_status), 2),
            to_ascii_hex(int(self._switches), 2))

    @property
    def device_category(self) -> DeviceCategory:
        """Category for the device."""
        return self._device_category

    @property
    def enable_status(self) -> ESFlags:
        """Flags indicating settings that have been enabled."""
        return self._enable_status

    @property
    def group_number(self) -> int:
        """Group number the device is assigned to."""
        return self._group_number

    @property
    def index(self) -> int:
        """Index of device within the category (also known as memory address)."""
        return self._index

    @property
    def name(self) -> str:
        """Provides the command name."""
        return CMD_DEVICE_PREFIX + self._device_category.id

    @property
    def switches(self) -> SwitchFlags:
        """Indicates switches that will be activated when device is triggered."""
        return self._switches

    @property
    def unit_number(self) -> int:
        """Unit number the device is assigned to (within group)."""
        return self._unit_number


class ChangeSpecialDeviceCommand(ChangeDeviceCommand):
    """
    Change settings for a 'Special' device on the base unit.

    This version is for the LS-30, which doesn't support separate control
    limit fields.
    """

    def __init__(self, device_category: DeviceCategory, index: int,
                 group_number: int, unit_number: int, enable_status: ESFlags,
                 switches: SwitchFlags, current_status: int, down_count: int,
                 message_attribute: int, current_reading: Union[int, float],
                 special_status: SSFlags, high_limit: Optional[Union[int, float]],
                 low_limit: Optional[Union[int, float]]):
        ChangeDeviceCommand.__init__(
            self, device_category, index, group_number, unit_number,
            enable_status, switches)
        self._current_status = current_status
        self._down_count = down_count
        self._message_attribute = message_attribute
        self._current_reading = current_reading
        self._special_status = special_status
        self._high_limit = high_limit
        self._low_limit = low_limit

    @property
    def action(self) -> str:
        """Provides the action to perform."""
        return ACTION_SET

    @property
    def args(self) -> str:
        """Provides arguments for the command."""
        return '{}{}{}{}{}{}{}{}{}{}{}'.format(
            to_ascii_hex(self._index, 2),
            to_ascii_hex(self._group_number, 2),
            to_ascii_hex(self._unit_number, 2),
            to_ascii_hex(int(self._enable_status), 4),
            to_ascii_hex(int(self._switches), 4),
            to_ascii_hex(self._current_status, 2),
            to_ascii_hex(self._down_count, 2),
            to_ascii_hex(encode_value_using_ma(self._message_attribute, self._current_reading), 2),
            to_ascii_hex(encode_value_using_ma(self._message_attribute, self._high_limit), 2),
            to_ascii_hex(encode_value_using_ma(self._message_attribute, self._low_limit), 2),
            to_ascii_hex(int(self._special_status), 2))

    @property
    def current_status(self) -> int:
        """Multi-purpose field containing RSSI reading and magnet sensor flag.
           Recommend using the 'rssi_db', 'rssi_bars' or 'is_closed' properties
           instead. """
        return self._current_status

    @property
    def down_count(self) -> int:
        """Supervisory down count timer.
           When this reaches zero, a 'Loss of Supervision-RF' event is raised."""
        return self._down_count

    @property
    def high_limit(self) -> Optional[Union[int, float]]:
        """High limit setting for a special sensor."""
        return self._high_limit

    @property
    def low_limit(self) -> Optional[Union[int, float]]:
        """Low limit setting for a special sensor."""
        return self._low_limit

    @property
    def message_attribute(self) -> int:
        """Message Attribute."""
        return self._message_attribute

    @property
    def name(self) -> str:
        """Provides the command name."""
        return CMD_DEVICE_PREFIX + self._device_category.id

    @property
    def special_status(self) -> SSFlags:
        """Special sensor status flags."""
        return self._special_status


class ChangeSpecial2DeviceCommand(ChangeSpecialDeviceCommand):
    """
    Change settings for a 'Special' device on the base unit.

    This version is for the LS-10/LS-20, which support separate control
    limit fields.
    """

    def __init__(self, device_category: DeviceCategory, index: int,
                 group_number: int, unit_number: int, enable_status: ESFlags,
                 switches: SwitchFlags, current_status: int, down_count: int,
                 message_attribute: int, current_reading: Union[int, float],
                 special_status: SSFlags, high_limit: Optional[Union[int, float]],
                 low_limit: Optional[Union[int, float]],
                 control_high_limit: Optional[Union[int, float]],
                 control_low_limit: Optional[Union[int, float]]):
        ChangeSpecialDeviceCommand.__init__(
            self, device_category, index, group_number, unit_number,
            enable_status, switches, current_status, down_count,
            message_attribute, current_reading, special_status,
            high_limit, low_limit)
        self._control_high_limit = control_high_limit
        self._control_low_limit = control_low_limit

    @property
    def control_high_limit(self) -> Optional[Union[int, float]]:
        """Control high limit setting for a special sensor."""
        return self._control_high_limit

    @property
    def args(self) -> str:
        """Provides arguments for the command."""
        return '{}{}{}'.format(
            ChangeSpecialDeviceCommand.args,
            to_ascii_hex(encode_value_using_ma(self._message_attribute, self._control_high_limit), 2),
            to_ascii_hex(encode_value_using_ma(self._message_attribute, self._control_low_limit), 2))

    @property
    def control_low_limit(self) -> Optional[Union[int, float]]:
        """Control low limit setting for a special sensor."""
        return self._control_low_limit


class AddDeviceCommand(Command):
    """Enroll new device on the LifeSOS base unit."""

    def __init__(self, device_category: DeviceCategory):
        self._device_category = device_category

    @property
    def action(self) -> str:
        """Provides the action to perform."""
        return ACTION_ADD

    @property
    def device_category(self) -> DeviceCategory:
        """Category for the device."""
        return self._device_category

    @property
    def name(self) -> str:
        """Provides the command name."""
        return CMD_DEVICE_PREFIX + self._device_category.id


class DeleteDeviceCommand(Command):
    """Delete an enrolled device."""

    def __init__(self, device_category: DeviceCategory, index: int):
        self._device_category = device_category
        self._index = index

    @property
    def action(self) -> str:
        """Provides the action to perform."""
        return ACTION_DEL

    @property
    def args(self) -> str:
        """Provides arguments for the command."""
        return to_ascii_hex(self._index, 2)

    @property
    def device_category(self) -> DeviceCategory:
        """Category for the device."""
        return self._device_category

    @property
    def index(self) -> int:
        """Index of device within the category (also known as memory address)."""
        return self._index

    @property
    def name(self) -> str:
        """Provides the command name."""
        return CMD_DEVICE_PREFIX + self._device_category.id


class ClearStatusCommand(Command):
    """Clear the alarm/warning LEDs on base unit and stop siren."""

    @property
    def name(self) -> str:
        """Provides the command name."""
        return CMD_CLEAR_STATUS


class GetROMVersionCommand(Command):
    """Command to get the ROM version string from the LifeSOS base unit."""

    @property
    def action(self) -> str:
        """Provides the action to perform."""
        return ACTION_GET

    @property
    def name(self) -> str:
        """Provides the command name."""
        return CMD_ROMVER


class GetExitDelayCommand(Command):
    """Command to get the exit delay from the LifeSOS base unit."""

    @property
    def action(self) -> str:
        """Provides the action to perform."""
        return ACTION_GET

    @property
    def name(self) -> str:
        """Provides the command name."""
        return CMD_EXIT_DELAY


class SetExitDelayCommand(Command):
    """Command to set the exit delay on the LifeSOS base unit."""

    def __init__(self, exit_delay: int):
        if exit_delay < 0x00:
            raise ValueError("Exit delay cannot be negative.")
        elif exit_delay > 0xff:
            raise ValueError("Exit delay cannot exceed %s seconds.", 0xff)
        self._exit_delay = exit_delay

    @property
    def action(self) -> str:
        """Provides the action to perform."""
        return ACTION_SET

    @property
    def args(self) -> str:
        """Provides arguments for the command."""
        return to_ascii_hex(self._exit_delay, 2)

    @property
    def exit_delay(self) -> int:
        """Exit delay (in seconds) on the LifeSOS base unit."""
        return self._exit_delay

    @property
    def name(self) -> str:
        """Provides the command name."""
        return CMD_EXIT_DELAY


class GetEntryDelayCommand(Command):
    """Command to get the entry delay from the LifeSOS base unit."""

    @property
    def action(self) -> str:
        """Provides the action to perform."""
        return ACTION_GET

    @property
    def name(self) -> str:
        """Provides the command name."""
        return CMD_ENTRY_DELAY


class SetEntryDelayCommand(Command):
    """Command to set the entry delay on the LifeSOS base unit."""

    def __init__(self, entry_delay: int):
        if entry_delay < 0x00:
            raise ValueError("Entry delay cannot be negative.")
        elif entry_delay > 0xff:
            raise ValueError("Entry delay cannot exceed %s seconds.", 0xff)
        self._entry_delay = entry_delay

    @property
    def action(self) -> str:
        """Provides the action to perform."""
        return ACTION_SET

    @property
    def args(self) -> str:
        """Provides arguments for the command."""
        return to_ascii_hex(self._entry_delay, 2)

    @property
    def entry_delay(self) -> int:
        """Entry delay (in seconds) on the LifeSOS base unit."""
        return self._entry_delay

    @property
    def name(self) -> str:
        """Provides the command name."""
        return CMD_ENTRY_DELAY


class GetSwitchCommand(Command):
    """Command to get the state of a switch."""

    def __init__(self, switch_number: SwitchNumber):
        self._switch_number = switch_number

    @property
    def action(self) -> str:
        """Provides the action to perform."""
        return ACTION_GET

    @property
    def name(self) -> str:
        """Provides the command name."""
        return CMD_SWITCH_PREFIX + to_ascii_hex(self._switch_number.value, 1)


class SetSwitchCommand(Command):
    """Command to set the state of a switch."""

    def __init__(self, switch_number: SwitchNumber, switch_state: SwitchState):
        self._switch_number = switch_number
        self._switch_state = switch_state

    @property
    def action(self) -> str:
        """Provides the action to perform."""
        return ACTION_SET

    @property
    def args(self) -> str:
        """Provides arguments for the command."""
        return to_ascii_hex(self._switch_state, 1)

    @property
    def name(self) -> str:
        """Provides the command name."""
        return CMD_SWITCH_PREFIX + to_ascii_hex(self._switch_number.value, 1)

    @property
    def switch_number(self) -> SwitchNumber:
        """Switch number on the LifeSOS base unit."""
        return self._switch_number

    @property
    def switch_state(self) -> SwitchState:
        """Switch state."""
        return self._switch_state


class GetEventLogCommand(Command):
    """Get an entry from the event log."""

    def __init__(self, index: int):
        self._index = index

    @property
    def index(self) -> int:
        """Index for entry in the event log."""
        return self._index

    @property
    def name(self) -> str:
        """Provides the command name."""
        return CMD_EVENT_LOG

    @property
    def args(self) -> str:
        """Provides arguments for the command."""
        return to_ascii_hex(self._index, 3)


class GetSensorLogCommand(Command):
    """Get an entry from the Special sensor log."""

    def __init__(self, index: int):
        self._index = index

    @property
    def index(self) -> int:
        """Index for entry in the sensor log."""
        return self._index

    @property
    def name(self) -> str:
        """Provides the command name."""
        return CMD_SENSOR_LOG

    @property
    def args(self) -> str:
        """Provides arguments for the command."""
        return to_ascii_hex(self._index, 3)
