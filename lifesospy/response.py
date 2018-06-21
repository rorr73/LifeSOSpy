from abc import ABC, abstractmethod
from datetime import datetime
from lifesospy.const import *
from lifesospy.devicecategory import *
from lifesospy.enums import *
from lifesospy.util import *
from typing import Optional, Union


class Response(ABC):
    """Represents response from a command issued to the LifeSOS base unit."""

    def __init__(self, text: str):
        self._text = text
        self._is_error = False

    @property
    @abstractmethod
    def command_name(self) -> str:
        """Provides the command name."""
        return ''

    @property
    def is_error(self) -> bool:
        """True if an error occurred; otherwise, False."""
        return self._is_error

    @property
    def text(self) -> str:
        """The original (undecoded) response text."""
        return self._text

    @staticmethod
    def parse(text) -> Optional['Response']:
        """Parse response into an instance of the appropriate child class."""

        # Trim the start and end markers, and ensure only lowercase is used
        if text.startswith(MARKER_START) and text.endswith(MARKER_END):
            text = text[1:len(text)-1].lower()

        # No-op; can just ignore these
        if len(text) == 0:
            return None

        if text.startswith(CMD_DATETIME):
            return DateTimeResponse(text)

        elif text.startswith(CMD_OPMODE):
            return OpModeResponse(text)

        elif text.startswith(CMD_DEVBYIDX_PREFIX):
            if RESPONSE_ERROR == text[2:] or text[2:4] == '00':
                return DeviceNotFoundResponse(text)
            else:
                return DeviceInfoResponse(text)

        elif text.startswith(CMD_DEVICE_PREFIX):
            action = next((a for a in [ACTION_ADD, ACTION_DEL, ACTION_SET] if a == text[2:3]), ACTION_NONE)
            args = text[2+len(action):]
            if RESPONSE_ERROR == args:
                return DeviceNotFoundResponse(text)
            elif action == ACTION_ADD:
                if len(args) == 0:
                    return DeviceAddingResponse(text)
                else:
                    return DeviceAddedResponse(text)
            elif action == ACTION_SET:
                return DeviceChangedResponse(text)
            elif action == ACTION_DEL:
                return DeviceDeletedResponse(text)
            else:
                return DeviceInfoResponse(text)

        elif text.startswith(CMD_CLEAR_STATUS):
            return ClearedStatusResponse(text)

        elif text.startswith(CMD_ROMVER):
            return ROMVersionResponse(text)

        elif text.startswith(CMD_EXIT_DELAY):
            return ExitDelayResponse(text)

        elif text.startswith(CMD_ENTRY_DELAY):
            return EntryDelayResponse(text)

        elif text.startswith(CMD_SWITCH_PREFIX) and SwitchNumber.has_value(from_ascii_hex(text[1:2])):
            return SwitchResponse(text)

        elif text.startswith(CMD_EVENT_LOG):
            if RESPONSE_ERROR == text[2:] or text[2:4] == '00':
                return EventLogNotFoundResponse(text)
            else:
                return EventLogResponse(text)

        elif text.startswith(CMD_SENSOR_LOG):
            if RESPONSE_ERROR == text[2:] or text[2:4] == '00':
                return SensorLogNotFoundResponse(text)
            else:
                return SensorLogResponse(text)

        else:
            raise ValueError("Response not recognised: " + text)

    def __repr__(self) -> str:
        return "<{}{}>".format(self.__class__.__name__,
                               "" if not self._is_error else " [ERROR]")


class DateTimeResponse(Response):
    """Response that provides the current date/time on the LifeSOS base unit."""

    def __init__(self, text: str):
        Response.__init__(self, text)
        text = text[len(CMD_DATETIME):]
        self._was_set = text.startswith(ACTION_SET)
        if self._was_set:
            text = text[1:]
        if len(text) != 11:
            raise ValueError("Date/Time response length is invalid.")
        self._remote_datetime = datetime.strptime(text[0:6] + text[7:11], '%y%m%d%H%M')

    @property
    def command_name(self) -> str:
        """Provides the command name."""
        return CMD_DATETIME

    @property
    def remote_datetime(self) -> datetime:
        """Date/Time on the LifeSOS base unit."""
        return self._remote_datetime

    @property
    def was_set(self) -> bool:
        """True if date/time was set on the base unit; otherwise, False."""
        return self._was_set

    def __repr__(self) -> str:
        return "<DateTimeResponse: Remote date/time {} {}{}>".\
            format('is' if not self._was_set else "was set to",
                   self._remote_datetime.strftime('%a %d %b %Y %I:%M %p'),
                   '' if not self._is_error else " [ERROR]")


class OpModeResponse(Response):
    """Response that provides the current operation mode on the LifeSOS base unit."""

    def __init__(self, text: str):
        Response.__init__(self, text)
        text = text[len(CMD_OPMODE):]
        self._was_set = text.startswith(ACTION_SET)
        if self._was_set:
            text = text[1:]
        self._operation_mode_value = int(text, 16)
        if OperationMode.has_value(self._operation_mode_value):
            self._operation_mode = OperationMode(self._operation_mode_value)
        else:
            self._operation_mode = None

    @property
    def command_name(self) -> str:
        """Provides the command name."""
        return CMD_OPMODE

    @property
    def operation_mode(self) -> OperationMode:
        """Operation mode on the LifeSOS base unit."""
        return self._operation_mode

    @property
    def was_set(self) -> bool:
        """True if operation mode was set on the base unit; otherwise, False."""
        return self._was_set

    def __repr__(self) -> str:
        return "<OpModeResponse: Operation mode {} {:x} ({}){}>".\
            format('is' if not self._was_set else "was set to",
                   self._operation_mode_value,
                   'Unknown' if self._operation_mode is None else self._operation_mode.name,
                   '' if not self._is_error else " [ERROR]")


class DeviceInfoResponse(Response):
    """Response that provides information for a device, and the settings that
       have been configured for it on the base unit."""

    def __init__(self, text: str):
        Response.__init__(self, text)
        self._command_name = text[0:2]
        self._device_category = DC_ALL_LOOKUP[text[1:2]]
        text = text[2:]
        if self._command_name.startswith(CMD_DEVICE_PREFIX):
            self._index = int(text[0:2], 16)
            text = text[2:]
        else:
            self._index = None
        self._device_type_value = int(text[0:2], 16)
        if DeviceType.has_value(self._device_type_value):
            self._device_type = DeviceType(self._device_type_value)
        else:
            self._device_type = None
        self._device_id = int(text[2:8], 16)
        self._message_attribute = int(text[8:10], 16)
        self._device_characteristics = DCFlags(int(text[10:12], 16))
        # self._?? = int(text[12:14], 16)
        self._group_number = int(text[14:16], 16)
        self._unit_number = int(text[16:18], 16)
        self._enable_status = ESFlags(int(text[18:22], 16))
        self._switches = SwitchFlags(int(text[22:26], 16))
        self._current_status = int(text[26:28], 16)
        self._down_count = int(text[28:30], 16)

        # Remaining fields used by the 'Special' sensors
        if len(text) > 30:
            self._current_reading = self._apply_ma_to_ss_value(int(text[30:32], 16))
            self._alarm_high_limit = self._apply_ma_to_ss_value(int(text[32:34], 16))
            self._alarm_low_limit = self._apply_ma_to_ss_value(int(text[34:36], 16))
            self._special_status = SSFlags(int(text[36:38], 16))
        else:
            self._current_reading = None
            self._alarm_high_limit = None
            self._alarm_low_limit = None
            self._special_status = None
        if len(text) > 38:
            # These don't exist on LS-30... they're LS-10/LS-20 only
            self._control_high_limit = self._apply_ma_to_ss_value(int(text[38:40], 16))
            self._control_low_limit = self._apply_ma_to_ss_value(int(text[40:42], 16))
        else:
            self._control_high_limit = None
            self._control_low_limit = None

    @property
    def alarm_high_limit(self) -> Optional[int]:
        """Alarm high limit setting for a special sensor."""
        return self._alarm_high_limit

    @property
    def alarm_low_limit(self) -> Optional[int]:
        """Alarm low limit setting for a special sensor."""
        return self._alarm_low_limit

    @property
    def command_name(self) -> str:
        """Provides the command name."""
        return self._command_name

    @property
    def control_high_limit(self) -> Optional[int]:
        """Control high limit setting for a special sensor."""
        return self._control_high_limit

    @property
    def control_low_limit(self) -> Optional[int]:
        """Control low limit setting for a special sensor."""
        return self._control_low_limit

    @property
    def current_reading(self) -> Optional[int]:
        """Current reading for a special sensor."""
        return self._current_reading

    @property
    def current_status(self) -> int:
        """Multi-purpose field containing RSSI reading and magnet sensor flag.
           Recommend using the 'rssi_db', 'rssi_bars' or 'is_closed' properties
           instead. """
        return self._current_status

    @property
    def device_category(self) -> DeviceCategory:
        """Category for the device."""
        return self._device_category

    @property
    def device_characteristics(self) -> DCFlags:
        """Flags indicating the device characteristics."""
        return self._device_characteristics

    @property
    def device_id(self) -> int:
        """Unique identifier for the device."""
        return self._device_id

    @property
    def device_type(self) -> Optional[DeviceType]:
        """Type of device."""
        return self._device_type

    @property
    def device_type_value(self) -> int:
        """Value that represents the type of device."""
        return self._device_type_value

    @property
    def down_count(self) -> int:
        """Supervisory down count timer.
           When this reaches zero, a 'Loss of Supervision-RF' event is raised."""
        return self._down_count

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
        """
        Index of device within the category (also known as memory address).

        Note it only exists in response to a GetDevice command, and will get
        out of sync if any devices above it are deleted.
        """
        return self._index

    @property
    def is_closed(self) -> Optional[bool]:
        """For Magnet Sensor; True if Closed, False if Open."""
        if self._device_type is not None and self._device_type == DeviceType.DoorMagnet:
            return bool(self._current_status & 0x01)
        else:
            return None

    @property
    def message_attribute(self) -> int:
        """Message Attribute."""
        return self._message_attribute

    @property
    def rssi_bars(self) -> int:
        """Received Signal Strength Indication, from 0 to 4 bars."""
        rssi_db = self.rssi_db
        if rssi_db < 45:
            return 0
        elif rssi_db < 60:
            return 1
        elif rssi_db < 75:
            return 2
        elif rssi_db < 90:
            return 3
        else:
            return 4

    @property
    def rssi_db(self) -> int:
        """Received Signal Strength Indication, in dB."""
        return max(min(self._current_status - 0x40, 99), 0)

    @property
    def special_status(self) -> Optional[SSFlags]:
        """Special sensor status flags."""
        return self._special_status

    @property
    def switches(self) -> SwitchFlags:
        """Indicates switches that will be activated when device is triggered."""
        return self._switches

    @property
    def unit_number(self) -> int:
        """Unit number the device is assigned to (within group)."""
        return self._unit_number

    @property
    def zone(self) -> str:
        """Zone the device is assigned to."""
        return '{:02x}-{:02x}'.format(self._group_number, self._unit_number)

    def __repr__(self) -> str:
        return "<DeviceInfoResponse: Id {:06x}, Type {:02x} ({}), Category '{}', Zone '{}', RSSI {} dB{}, {}, {}, {}{}>".\
            format(self._device_id,
                   self._device_type_value,
                   'Unknown' if self._device_type is None else self._device_type.name,
                   self._device_category.description,
                   self.zone,
                   self.rssi_db,
                   '' if self._device_type_value != DeviceType.DoorMagnet else ", IsClosed={}".format(self.is_closed),
                   str(self._device_characteristics),
                   str(self._enable_status),
                   str(self._switches),
                   '' if not self._is_error else " [ERROR]")

    def _apply_ma_to_ss_value(self, value: int) -> Optional[Union[int, float]]:
        # Message attribute dictates how to determine the limit values
        if self._message_attribute == MA_TX3AC_100A:
            if value == 0xfe:
                return None
            else:
                return value
        elif self._message_attribute == MA_TX3AC_10A:
            if value == 0xfe:
                return None
            else:
                return value / 10
        else:
            if value == 0x80:
                return None
            elif value >= 0x80:
                return 0 - (0x100 - value)
            else:
                return value


class DeviceSettingsResponse(Response):
    """Settings configured in base unit for a device."""

    def __init__(self, text: str):
        Response.__init__(self, text)
        self._command_name = text[0:2]
        self._device_category = DC_ALL_LOOKUP[text[1:2]]
        text = text[3:]
        self._index = int(text[0:2], 16)
        self._group_number = int(text[2:4], 16)
        self._unit_number = int(text[4:6], 16)
        self._enable_status = ESFlags(int(text[6:10], 16))
        self._switches = SwitchFlags(int(text[10:14], 16))

        # Don't own a Special sensor to test this, so leave for now
        # if len(text) > 14:
        #     self._current_status = int(text[14:16], 16)
        #     self._down_count = int(text[16:18], 16)
        #     self._current_reading = int(text[18:20], 16)
        #     self._alarm_high_limit = int(text[20:22], 16)
        #     self._alarm_low_limit = int(text[22:24], 16)
        #     self._special_status = SSFlags(int(text[24:26], 16))
        # else:
        #     self._current_status = None
        #     self._down_count = None
        #     self._current_reading = None
        #     self._alarm_high_limit = None
        #     self._alarm_low_limit = None
        #     self._special_status = None
        # if len(text) > 26:
        #     self._control_high_limit = int(text[26:28], 16)
        #     self._control_low_limit = int(text[28:30], 16)
        # else:
        #     self._control_high_limit = None
        #     self._control_low_limit = None

    @property
    def command_name(self) -> str:
        """Provides the command name."""
        return self._command_name

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
        """Index of device within the category."""
        return self._index

    @property
    def switches(self) -> SwitchFlags:
        """Indicates switches that will be activated when device is triggered."""
        return self._switches

    @property
    def unit_number(self) -> int:
        """Unit number the device is assigned to (within group)."""
        return self._unit_number

    @property
    def zone(self) -> str:
        """Zone the device is assigned to."""
        return '{:02x}-{:02x}'.format(self._group_number, self._unit_number)

    def __repr__(self) -> str:
        return "<{}: Category '{}', Zone '{}', Index #{}, {}, {}>". \
            format(self.__class__.__name__,
                   self._device_category.description,
                   self.zone,
                   self._index,
                   str(self._enable_status),
                   str(self._switches))


class DeviceNotFoundResponse(Response):
    """Response that indicates there was no device at specified index or zone."""

    def __init__(self, text: str):
        Response.__init__(self, text)
        self._command_name = text[0:2]
        self._device_category = DC_ALL_LOOKUP[text[1:2]]

    @property
    def command_name(self) -> str:
        """Provides the command name."""
        return self._command_name

    @property
    def device_category(self) -> DeviceCategory:
        """Category for the device."""
        return self._device_category

    def __repr__(self) -> str:
        return "<DeviceNotFoundResponse: Get '{}', Category '{}'{}>".\
            format("By Index" if self._command_name.startswith(CMD_DEVBYIDX_PREFIX) else "By Zone",
                   self._device_category.description,
                   '' if not self._is_error else " [ERROR]")


class DeviceAddingResponse(Response):
    """Response indicating the base unit is now waiting for a device to enroll."""

    def __init__(self, text: str):
        Response.__init__(self, text)
        self._command_name = text[0:2]
        self._device_category = DC_ALL_LOOKUP[text[1:2]]

    @property
    def command_name(self) -> str:
        """Provides the command name."""
        return self._command_name

    @property
    def device_category(self) -> DeviceCategory:
        """Category for the device."""
        return self._device_category

    def __repr__(self) -> str:
        return "<DeviceAddingResponse: Category '{}'>".\
            format(self._device_category.description)


class DeviceAddedResponse(DeviceSettingsResponse):
    """Response that indicates a new device was successfully enrolled."""

    def __init__(self, text: str):
        DeviceSettingsResponse.__init__(self, text)


class DeviceChangedResponse(DeviceSettingsResponse):
    """Response that indicates device settings were changed."""

    def __init__(self, text: str):
        DeviceSettingsResponse.__init__(self, text)


class DeviceDeletedResponse(Response):
    """Response that indicates a device was deleted."""

    def __init__(self, text: str):
        Response.__init__(self, text)
        self._command_name = text[0:2]
        self._device_category = DC_ALL_LOOKUP[text[1:2]]
        text = text[3:]
        self._index = int(text[0:2], 16)

    @property
    def command_name(self) -> str:
        """Provides the command name."""
        return self._command_name

    @property
    def device_category(self) -> DeviceCategory:
        """Category for the device."""
        return self._device_category

    @property
    def index(self) -> int:
        """Index of device within the category."""
        return self._index

    def __repr__(self) -> str:
        return "<DeviceDeletedResponse: Category '{}', Index #{}>".\
            format(self._device_category.description,
                   self._index)


class ClearedStatusResponse(Response):
    """Response that indicates status was cleared on base unit."""

    def __init__(self, text: str):
        Response.__init__(self, text)

    @property
    def command_name(self) -> str:
        return CMD_CLEAR_STATUS

    def __repr__(self) -> str:
        return "<ClearedStatusResponse: Cleared status on base unit{}>".\
            format('' if not self._is_error else " [ERROR]")


class ROMVersionResponse(Response):
    """Response that provides the ROM version on the base unit."""

    def __init__(self, text: str):
        Response.__init__(self, text)
        text = text[len(CMD_ROMVER):]
        self._version = text

    @property
    def command_name(self) -> str:
        """Provides the command name."""
        return CMD_ROMVER

    @property
    def version(self) -> str:
        """ROM version string."""
        return self._version

    def __repr__(self) -> str:
        return "<ROMVersionResponse: '{}'{}>".format(
            self._version,
            '' if not self._is_error else " [ERROR]")


class ExitDelayResponse(Response):
    """Response that provides the current exit delay on the LifeSOS base unit."""

    def __init__(self, text: str):
        Response.__init__(self, text)
        text = text[len(CMD_EXIT_DELAY):]
        self._was_set = text.startswith(ACTION_SET)
        if self._was_set:
            text = text[1:]
        self._exit_delay = from_ascii_hex(text)

    @property
    def command_name(self) -> str:
        """Provides the command name."""
        return CMD_EXIT_DELAY

    @property
    def exit_delay(self) -> int:
        """Exit delay (in seconds) on the LifeSOS base unit."""
        return self._exit_delay

    @property
    def was_set(self) -> bool:
        """True if exit delay was set on the base unit; otherwise, False."""
        return self._was_set

    def __repr__(self) -> str:
        return "<ExitDelayResponse: Exit delay {} {} seconds{}>".\
            format('is' if not self._was_set else "was set to",
                   self._exit_delay,
                   '' if not self._is_error else " [ERROR]")


class EntryDelayResponse(Response):
    """Response that provides the current entry delay on the LifeSOS base unit."""

    def __init__(self, text: str):
        Response.__init__(self, text)
        text = text[len(CMD_ENTRY_DELAY):]
        self._was_set = text.startswith(ACTION_SET)
        if self._was_set:
            text = text[1:]
        self._entry_delay = from_ascii_hex(text)

    @property
    def command_name(self) -> str:
        """Provides the command name."""
        return CMD_ENTRY_DELAY

    @property
    def entry_delay(self) -> int:
        """Entry delay (in seconds) on the LifeSOS base unit."""
        return self._entry_delay

    @property
    def was_set(self) -> bool:
        """True if entry delay was set on the base unit; otherwise, False."""
        return self._was_set

    def __repr__(self) -> str:
        return "<EntryDelayResponse: Entry delay {} {} seconds{}>".\
            format('is' if not self._was_set else "was set to",
                   self._entry_delay,
                   '' if not self._is_error else " [ERROR]")


class SwitchResponse(Response):
    """Response that provides the state of a switch on the LifeSOS base unit."""

    def __init__(self, text: str):
        Response.__init__(self, text)
        self._switch_number = SwitchNumber(from_ascii_hex(text[1:2]))
        text = text[2:]
        self._was_set = text.startswith(ACTION_SET)
        if self._was_set:
            text = text[1:]
        self._switch_state_value = from_ascii_hex(text[0:1])
        if SwitchState.has_value(self._switch_state_value):
            self._switch_state = SwitchState(self._switch_state_value)
        else:
            self._switch_state = None
        if RESPONSE_ERROR == text[1:]:
            self._is_error = True

    @property
    def command_name(self) -> str:
        """Provides the command name."""
        return CMD_SWITCH_PREFIX + to_ascii_hex(self._switch_number.value, 1)

    @property
    def switch_number(self) -> SwitchNumber:
        """Switch number on the LifeSOS base unit."""
        return self._switch_number

    @property
    def switch_state(self) -> Optional[SwitchState]:
        """Switch state."""
        return self._switch_state

    @property
    def switch_state_value(self) -> int:
        """Value that represents the switch state."""
        return self._switch_state_value

    @property
    def was_set(self) -> bool:
        """True if switch state was set on the base unit; otherwise, False."""
        return self._was_set

    def __repr__(self) -> str:
        return "<SwitchResponse: {} {} 0x{:01x} ({}){}>".\
            format(self._switch_number.name,
                   'is' if not self._was_set else "was set to",
                   self._switch_state_value,
                   'Unknown' if self._switch_state is None else self._switch_state.name,
                   '' if not self._is_error else " [ERROR]")


class EventLogResponse(Response):
    """Response that provides an entry from the event log."""

    def __init__(self, text: str):
        Response.__init__(self, text)
        text = text[len(CMD_EVENT_LOG):]
        self._event_qualifier_value = int(text[0:1], 16)
        if ContactIDEventQualifier.has_value(self._event_qualifier_value):
            self._event_qualifier = ContactIDEventQualifier(self._event_qualifier_value)
        else:
            self._event_qualifier = None
        self._event_code_value = int(text[1:4], 16)
        if ContactIDEventCode.has_value(self._event_code_value):
            self._event_code = ContactIDEventCode(self._event_code_value)
        else:
            self._event_code = None
        group_partition = int(text[4:6], 16)
        # self._?? = int(text[6:7], 16)
        self._device_category = DC_ALL[int(text[7:8], 16)]
        zone_user = int(text[8:10], 16)
        if self._device_category == DC_BASEUNIT:
            self._group_number = None
            self._unit_number = None
            self._user_id = zone_user if zone_user != 0 else None
        else:
            self._group_number = group_partition
            self._unit_number = zone_user
            self._user_id = None
        self._action = DC_ALL[int(text[10:12], 16)]
        self._logged_date = text[12:14] + '/' + text[14:16]
        self._logged_time = text[16:18] + ':' + text[18:20]
        self._last_index = int(text[20:23], 16)

    @property
    def action(self) -> DeviceCategory:
        """
        Category of device that originated the event.

        From what I can tell, this is the same as device_category except
        when changing operation mode via keypad or ethernet interface. In this
        one case, device_category=='baseunit' and action=='controller'.
        """
        return self._action

    @property
    def command_name(self) -> str:
        """Provides the command name."""
        return CMD_EVENT_LOG

    @property
    def device_category(self) -> DeviceCategory:
        """Category for the device."""
        return self._device_category

    @property
    def event_code(self) -> Optional[ContactIDEventCode]:
        """Type of event."""
        return self._event_code

    @property
    def event_code_value(self) -> int:
        """Value that represents the type of event."""
        return self._event_code_value

    @property
    def event_qualifier(self) -> Optional[ContactIDEventQualifier]:
        """Provides context for the type of event."""
        return self._event_qualifier

    @property
    def event_qualifier_value(self) -> int:
        """Value that represents the context for the type of event."""
        return self._event_qualifier_value

    @property
    def group_number(self) -> Optional[int]:
        """Group number the device is assigned to."""
        return self._group_number

    @property
    def last_index(self) -> int:
        """Index for the last entry in the event log."""
        return self._last_index

    @property
    def logged_date(self) -> str:
        """Date the event was logged; mm/dd format, year omitted."""
        return self._logged_date

    @property
    def logged_time(self) -> str:
        """Time the event was logged; HH:MM format."""
        return self._logged_time

    @property
    def unit_number(self) -> Optional[int]:
        """Unit number the device is assigned to (within group)."""
        return self._unit_number

    @property
    def user_id(self) -> Optional[int]:
        """Identifies the user."""
        return self._user_id

    @property
    def zone(self) -> Optional[str]:
        """Zone the device is assigned to."""
        if self._device_category == DC_BASEUNIT:
            return None
        else:
            return '{:02x}-{:02x}'.format(self._group_number, self._unit_number)

    def __repr__(self) -> str:
        zone_user = ''
        if self.zone is not None:
            zone_user = ", Zone '{}'".format(self.zone)
        elif self._user_id is not None:
            zone_user = ", User {:02x}".format(self._user_id)
        return "<{}: {} {:03x} ({}), Category '{}'{}, Logged '{} {}'>". \
            format(self.__class__.__name__,
                   self._event_qualifier_value if not self._event_qualifier else self._event_qualifier.name,
                   self._event_code_value,
                   "Unknown" if not self._event_code else self._event_code.name,
                   self._device_category.description,
                   zone_user,
                   self._logged_date,
                   self._logged_time)


class EventLogNotFoundResponse(Response):
    """Response that indicates there was no entry in event log at specified index."""

    def __init__(self, text: str):
        Response.__init__(self, text)

    @property
    def command_name(self) -> str:
        """Provides the command name."""
        return CMD_EVENT_LOG


class SensorLogResponse(Response):
    """Response that provides an entry from the Special sensor log."""

    def __init__(self, text: str):
        Response.__init__(self, text)
        text = text[len(CMD_SENSOR_LOG):]
        self._group_number = int(text[0:2], 16)
        self._unit_number = int(text[2:4], 16)
        self._logged_date = text[4:6]
        self._logged_time = text[6:8] + ':' + text[8:10]
        # I'm guessing this was created before the AC Power Meter TX-3AC,
        # since the message_attribute doesn't exist and the reading cannot
        # be adjusted accordingly.
        self._reading = int(text[10:12], 16)
        if self._reading == 0x80:
            self._reading = None
        elif self._reading >= 0x80:
            self._reading = 0 - (0x100 - self._reading)
        self._last_index = int(text[12:15], 16)

    @property
    def command_name(self) -> str:
        """Provides the command name."""
        return CMD_SENSOR_LOG

    @property
    def group_number(self) -> int:
        """Group number the device is assigned to."""
        return self._group_number

    @property
    def last_index(self) -> int:
        """Index for the last entry in the sensor log."""
        return self._last_index

    @property
    def logged_date(self) -> str:
        """Date the event was logged; dd format, month and year omitted."""
        return self._logged_date

    @property
    def logged_time(self) -> str:
        """Time the event was logged; HH:MM format."""
        return self._logged_time

    @property
    def reading(self) -> Optional[int]:
        """Reading."""
        return self._reading

    @property
    def unit_number(self) -> int:
        """Unit number the device is assigned to (within group)."""
        return self._unit_number

    @property
    def zone(self) -> Optional[str]:
        """Zone the device is assigned to."""
        return '{:02x}-{:02x}'.format(self._group_number, self._unit_number)

    def __repr__(self) -> str:
        return "<{}: Zone '{}', Reading {}, Logged '{}/{}'>". \
            format(self.__class__.__name__,
                   self.zone,
                   self._reading,
                   self._logged_date,
                   self._logged_time)


class SensorLogNotFoundResponse(Response):
    """Response that indicates there was no entry in Special sensor log at specified index."""

    def __init__(self, text: str):
        Response.__init__(self, text)

    @property
    def command_name(self) -> str:
        """Provides the command name."""
        return CMD_SENSOR_LOG
