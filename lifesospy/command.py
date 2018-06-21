from abc import ABC, abstractmethod
from datetime import datetime
from lifesospy.const import *
from lifesospy.devicecategory import *
from lifesospy.enums import *
from lifesospy.util import *


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
        return "<{}: '{}'>".format(self.__class__.__name__,
                                   self.format())


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
        return '{:02x}{:02x}'.format(self._group_number, self._unit_number)

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
        return '{:02x}{:02x}{:02x}{:04x}{:04x}'.format(
            self._index, self._group_number, self._unit_number,
            int(self._enable_status), int(self._switches))

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
    """Change settings for a 'Special' device on the base unit."""

    def __init__(self, device_category: DeviceCategory, index: int,
                 group_number: int, unit_number: int, enable_status: ESFlags,
                 switches: SwitchFlags, special_status: SSFlags,
                 alarm_high_limit: Optional[int], alarm_low_limit: Optional[int],
                 control_high_limit: Optional[int], control_low_limit: Optional[int]):
        ChangeDeviceCommand.__init__(
            self, device_category, index, group_number, unit_number,
            enable_status, switches)
        self._special_status = special_status
        self._alarm_high_limit = alarm_high_limit
        self._alarm_low_limit = alarm_low_limit
        self._control_high_limit = control_high_limit
        self._control_low_limit = control_low_limit

    @property
    def action(self) -> str:
        """Provides the action to perform."""
        return ACTION_SET

    @property
    def args(self) -> str:
        """Provides arguments for the command."""
        return '{:02x}{:02x}{:02x}{:04x}{:04x}'.format(
            self._index, self._group_number, self._unit_number,
            int(self._enable_status), int(self._switches))

    @property
    def alarm_high_limit(self) -> Optional[int]:
        """Alarm high limit setting for a special sensor."""
        return self._alarm_high_limit

    @property
    def alarm_low_limit(self) -> Optional[int]:
        """Alarm low limit setting for a special sensor."""
        return self._alarm_low_limit

    @property
    def control_high_limit(self) -> Optional[int]:
        """Control high limit setting for a special sensor."""
        return self._control_high_limit

    @property
    def control_low_limit(self) -> Optional[int]:
        """Control low limit setting for a special sensor."""
        return self._control_low_limit

    @property
    def name(self) -> str:
        """Provides the command name."""
        return CMD_DEVICE_PREFIX + self._device_category.id

    @property
    def special_status(self) -> Optional[SSFlags]:
        """Special sensor status flags."""
        return self._special_status


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
