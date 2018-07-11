"""
This module contains all of the responses that can be received from the base unit.
"""

from abc import ABC, abstractmethod
from datetime import datetime, time
from typing import Optional, Union, Dict, Any
from lifesospy.const import (
    MARKER_START, MARKER_END, CMD_DATETIME, CMD_OPMODE, CMD_DEVBYIDX_PREFIX,
    CMD_DEVICE_PREFIX, CMD_CLEAR_STATUS, CMD_ROMVER, CMD_EXIT_DELAY,
    CMD_ENTRY_DELAY, CMD_EVENT_LOG, CMD_SENSOR_LOG, CMD_SWITCH_PREFIX,
    ACTION_NONE, ACTION_SET, ACTION_ADD, ACTION_DEL, MA_NONE, RESPONSE_ERROR)
from lifesospy.devicecategory import (
    DeviceCategory, DC_ALL, DC_ALL_LOOKUP, DC_BASEUNIT, DC_SPECIAL)
from lifesospy.enums import (
    OperationMode, DeviceType, DCFlags, ESFlags, SSFlags, SwitchFlags,
    SwitchNumber, SwitchState, ContactIDEventQualifier, ContactIDEventCode)
from lifesospy.util import (
    is_ascii_hex, serializable, from_ascii_hex, to_ascii_hex,
    decode_value_using_ma)


class Response(ABC):
    """Represents response from a command issued to the LifeSOS base unit."""

    def __init__(self):
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

    @staticmethod
    def parse(text) -> Optional['Response']:
        """Parse response into an instance of the appropriate child class."""

        # Trim the start and end markers, and ensure only lowercase is used
        if text.startswith(MARKER_START) and text.endswith(MARKER_END):
            text = text[1:len(text)-1].lower()

        # No-op; can just ignore these
        if not text:
            return None

        if text.startswith(CMD_DATETIME):
            return DateTimeResponse(text)

        elif text.startswith(CMD_OPMODE):
            return OpModeResponse(text)

        elif text.startswith(CMD_DEVBYIDX_PREFIX):
            if RESPONSE_ERROR == text[2:] or text[2:4] == '00':
                return DeviceNotFoundResponse(text)
            return DeviceInfoResponse(text)

        elif text.startswith(CMD_DEVICE_PREFIX):
            action = next((a for a in [ACTION_ADD, ACTION_DEL, ACTION_SET]
                           if a == text[2:3]), ACTION_NONE)
            args = text[2+len(action):]
            if RESPONSE_ERROR == args:
                return DeviceNotFoundResponse(text)
            elif action == ACTION_ADD:
                if not args:
                    return DeviceAddingResponse(text)
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

        elif text.startswith(CMD_SWITCH_PREFIX) and is_ascii_hex(text[1:2]):
            return SwitchResponse(text)

        elif text.startswith(CMD_EVENT_LOG):
            if RESPONSE_ERROR == text[2:]:
                return EventLogNotFoundResponse(text)
            return EventLogResponse(text)

        elif text.startswith(CMD_SENSOR_LOG):
            if RESPONSE_ERROR == text[2:]:
                return SensorLogNotFoundResponse(text)
            return SensorLogResponse(text)

        else:
            raise ValueError("Response not recognised: " + text)

    def __repr__(self) -> str:
        return "<{}{}>".format(
            self.__class__.__name__,
            '' if not self._is_error else ": is_error")

    def as_dict(self) -> Dict[str, Any]:
        """Converts to a dict of attributes for easier serialization."""
        return serializable(self)


class DateTimeResponse(Response):
    """Response that provides the current date/time on the LifeSOS base unit."""

    def __init__(self, text: str):
        Response.__init__(self)
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
        return "{}: remote_datetime={}{}{}>".\
            format(self.__class__.__name__,
                   self._remote_datetime.strftime('%a %d %b %Y %I:%M %p'),
                   '' if not self._was_set else ", was_set",
                   '' if not self._is_error else ", is_error")


class OpModeResponse(Response):
    """Response that provides the current operation mode on the LifeSOS base unit."""

    def __init__(self, text: str):
        Response.__init__(self)
        text = text[len(CMD_OPMODE):]
        self._was_set = text.startswith(ACTION_SET)
        if self._was_set:
            text = text[1:]
        self._operation_mode_value = from_ascii_hex(text)
        self._operation_mode = OperationMode.parseint(
            self._operation_mode_value)

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
        return "<{}: operation_mode_value={:x}, operation_mode={}{}{}>".\
            format(self.__class__.__name__,
                   self._operation_mode_value,
                   str(self._operation_mode),
                   '' if not self._was_set else ", was_set",
                   '' if not self._is_error else ", is_error")


class DeviceInfoResponse(Response):
    """Response that provides information for a device, and the settings that
       have been configured for it on the base unit."""

    def __init__(self, text: str):
        Response.__init__(self)
        self._command_name = text[0:2]
        self._device_category = DC_ALL_LOOKUP[text[1:2]]
        text = text[2:]
        if self._command_name.startswith(CMD_DEVICE_PREFIX):
            self._index = from_ascii_hex(text[0:2])
            text = text[2:]
        else:
            self._index = None
        self._device_type_value = from_ascii_hex(text[0:2])
        self._device_type = DeviceType.parseint(self._device_type_value)
        self._device_id = from_ascii_hex(text[2:8])
        self._message_attribute = from_ascii_hex(text[8:10])
        self._device_characteristics = DCFlags(from_ascii_hex(text[10:12]))
        # self._?? = from_ascii_hex(text[12:14])
        self._group_number = from_ascii_hex(text[14:16])
        self._unit_number = from_ascii_hex(text[16:18])
        self._enable_status = ESFlags(from_ascii_hex(text[18:22]))
        self._switches = SwitchFlags(from_ascii_hex(text[22:26]))
        self._current_status = from_ascii_hex(text[26:28])
        self._down_count = from_ascii_hex(text[28:30])

        # Remaining fields used by the 'Special' sensors
        if len(text) > 30:
            self._current_reading = decode_value_using_ma(
                self._message_attribute, from_ascii_hex(text[30:32]))
            self._high_limit = decode_value_using_ma(
                self._message_attribute, from_ascii_hex(text[32:34]))
            self._low_limit = decode_value_using_ma(
                self._message_attribute, from_ascii_hex(text[34:36]))
            self._special_status = SSFlags(from_ascii_hex(text[36:38]))
        else:
            self._current_reading = None
            self._high_limit = None
            self._low_limit = None
            self._special_status = None
        if len(text) > 38:
            # These don't exist on LS-30... they're LS-10/LS-20 only
            self._control_high_limit = decode_value_using_ma(
                self._message_attribute, from_ascii_hex(text[38:40]))
            self._control_low_limit = decode_value_using_ma(
                self._message_attribute, from_ascii_hex(text[40:42]))
            self._control_limit_fields_exist = True
        else:
            self._control_high_limit = None
            self._control_low_limit = None
            self._control_limit_fields_exist = False

    @property
    def command_name(self) -> str:
        """Provides the command name."""
        return self._command_name

    @property
    def control_high_limit(self) -> Optional[Union[int, float]]:
        """Control high limit setting for a special sensor."""
        return self._control_high_limit

    @property
    def control_limit_fields_exist(self) -> bool:
        """True if control limit fields exist in response; otherwise, False."""
        return self._control_limit_fields_exist

    @property
    def control_low_limit(self) -> Optional[Union[int, float]]:
        """Control low limit setting for a special sensor."""
        return self._control_low_limit

    @property
    def current_reading(self) -> Optional[Union[int, float]]:
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
    def high_limit(self) -> Optional[Union[int, float]]:
        """High limit setting for a special sensor."""
        return self._high_limit

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
        return None

    @property
    def low_limit(self) -> Optional[Union[int, float]]:
        """Low limit setting for a special sensor."""
        return self._low_limit

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
        if self._device_category == DC_SPECIAL:
            special = ", current_reading={}, special_status={}, high_limit={}, low_limit={}".format(
                self._current_reading,
                str(self._special_status),
                self._high_limit,
                self._low_limit)
            if self._control_limit_fields_exist:
                special += ", control_high_limit={}, control_low_limit={}".format(
                    self._control_high_limit,
                    self._control_low_limit)
        else:
            special = ''
        return "<{}: device_id={:06x}, device_type_value={:02x}, device_type={}, " \
               "device_category.description={}, zone={}, rssi_db={}{}, " \
               "device_characteristics={}, enable_status={}, switches={}{}{}>".format(
                   self.__class__.__name__, self._device_id, self._device_type_value,
                   str(self._device_type), self._device_category.description, self.zone,
                   self.rssi_db,
                   '' if self._device_type_value != DeviceType.DoorMagnet else
                   ", is_closed={}".format(self.is_closed),
                   str(self._device_characteristics), str(self._enable_status),
                   str(self._switches), special,
                   '' if not self._is_error else ", is_error")


class DeviceSettingsResponse(Response):
    """Settings configured in base unit for a device."""

    def __init__(self, text: str):
        Response.__init__(self)
        self._command_name = text[0:2]
        self._device_category = DC_ALL_LOOKUP[text[1:2]]
        text = text[3:]
        self._index = from_ascii_hex(text[0:2])
        self._group_number = from_ascii_hex(text[2:4])
        self._unit_number = from_ascii_hex(text[4:6])
        self._enable_status = ESFlags(from_ascii_hex(text[6:10]))
        self._switches = SwitchFlags(from_ascii_hex(text[10:14]))

        # Remaining fields used by the 'Special' sensors (though only appear
        # in the changed response, not added response). Note that we don't
        # have a message attribute, so values must be decoded by receiver.
        if len(text) > 14:
            self._current_status = from_ascii_hex(text[14:16])
            self._down_count = from_ascii_hex(text[16:18])
            self._current_reading_encoded = from_ascii_hex(text[18:20])
            self._high_limit_encoded = from_ascii_hex(text[20:22])
            self._low_limit_encoded = from_ascii_hex(text[22:24])
            self._special_status = SSFlags(from_ascii_hex(text[24:26]))
            self._special_fields_exist = True
        else:
            self._current_status = None
            self._down_count = None
            self._current_reading_encoded = None
            self._high_limit_encoded = None
            self._low_limit_encoded = None
            self._special_status = None
            self._special_fields_exist = False
        if len(text) > 26:
            self._control_high_limit_encoded = from_ascii_hex(text[26:28])
            self._control_low_limit_encoded = from_ascii_hex(text[28:30])
            self._control_limit_fields_exist = True
        else:
            self._control_high_limit_encoded = None
            self._control_low_limit_encoded = None
            self._control_limit_fields_exist = False

    @property
    def command_name(self) -> str:
        """Provides the command name."""
        return self._command_name

    @property
    def control_high_limit_encoded(self) -> Optional[int]:
        """
        Control high limit setting for a special sensor.
        Must be decoded using message attribute from the device.
        """
        return self._control_high_limit_encoded

    @property
    def control_limit_fields_exist(self) -> bool:
        """True if control limit fields exist in response; otherwise, False."""
        return self._control_limit_fields_exist

    @property
    def control_low_limit_encoded(self) -> Optional[int]:
        """
        Control low limit setting for a special sensor.
        Must be decoded using message attribute from the device.
        """
        return self._control_low_limit_encoded

    @property
    def current_reading_encoded(self) -> Optional[int]:
        """
        Current reading for a special sensor.
        Must be decoded using message attribute from the device.
        """
        return self._current_reading_encoded

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
    def high_limit_encoded(self) -> Optional[int]:
        """
        High limit setting for a special sensor.
        Must be decoded using message attribute from the device.
        """
        return self._high_limit_encoded

    @property
    def index(self) -> int:
        """Index of device within the category."""
        return self._index

    @property
    def low_limit_encoded(self) -> Optional[int]:
        """
        Low limit setting for a special sensor.
        Must be decoded using message attribute from the device.
        """
        return self._low_limit_encoded

    @property
    def special_fields_exist(self) -> bool:
        """True if special fields exist in response; otherwise, False."""
        return self._special_fields_exist

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
        if self._special_fields_exist:
            special = \
                ", current_reading_encoded={}, special_status={}, " \
                "high_limit_encoded={}, low_limit_encoded={}".format(
                    self._current_reading_encoded,
                    str(self._special_status),
                    self._high_limit_encoded,
                    self._low_limit_encoded)
            if self._control_limit_fields_exist:
                special += ", control_high_limit_encoded={}, control_low_limit_encoded={}".format(
                    self._control_high_limit_encoded,
                    self._control_low_limit_encoded)
        else:
            special = ''
        return "<{}: device_category.description={}, zone={}, index={}, " \
               "enable_status={}, switches={}{}>".format(
                   self.__class__.__name__,
                   self._device_category.description,
                   self.zone,
                   self._index,
                   str(self._enable_status),
                   str(self._switches),
                   special)


class DeviceNotFoundResponse(Response):
    """Response that indicates there was no device at specified index or zone."""

    def __init__(self, text: str):
        Response.__init__(self)
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
        return "<{}: device_category.description={}{}>".\
            format(self.__class__.__name__,
                   self._device_category.description,
                   '' if not self._is_error else ", is_error")


class DeviceAddingResponse(Response):
    """Response indicating the base unit is now waiting for a device to enroll."""

    def __init__(self, text: str):
        Response.__init__(self)
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
        return "<{}: device_category.description={}>".\
            format(self.__class__.__name__,
                   self._device_category.description)


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
        Response.__init__(self)
        self._command_name = text[0:2]
        self._device_category = DC_ALL_LOOKUP[text[1:2]]
        text = text[3:]
        self._index = from_ascii_hex(text[0:2])

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
        return "<{}: device_category.description='{}', index={}>".\
            format(self.__class__.__name__,
                   self._device_category.description,
                   self._index)


class ClearedStatusResponse(Response):
    """Response that indicates status was cleared on base unit."""

    def __init__(self, text: str):
        Response.__init__(self)

    @property
    def command_name(self) -> str:
        return CMD_CLEAR_STATUS


class ROMVersionResponse(Response):
    """Response that provides the ROM version on the base unit."""

    def __init__(self, text: str):
        Response.__init__(self)
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
        return "<{}: version={}{}>".format(
            self.__class__.__name__,
            self._version,
            '' if not self._is_error else ", is_error")


class ExitDelayResponse(Response):
    """Response that provides the current exit delay on the LifeSOS base unit."""

    def __init__(self, text: str):
        Response.__init__(self)
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
        return "<{}: exit_delay={}{}{}>".\
            format(self.__class__.__name__,
                   self._exit_delay,
                   '' if not self._was_set else ", was_set",
                   '' if not self._is_error else ", is_error")


class EntryDelayResponse(Response):
    """Response that provides the current entry delay on the LifeSOS base unit."""

    def __init__(self, text: str):
        Response.__init__(self)
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
        return "<{}: entry_delay={}{}{}>".\
            format(self.__class__.__name__,
                   self._entry_delay,
                   '' if not self._was_set else ", was_set",
                   '' if not self._is_error else ", is_error")


class SwitchResponse(Response):
    """Response that provides the state of a switch on the LifeSOS base unit."""

    def __init__(self, text: str):
        Response.__init__(self)
        self._switch_number = SwitchNumber(from_ascii_hex(text[1:2]))
        text = text[2:]
        self._was_set = text.startswith(ACTION_SET)
        if self._was_set:
            text = text[1:]
        self._switch_state_value = from_ascii_hex(text[0:1])
        self._switch_state = SwitchState.parseint(self._switch_state_value)
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
        return "<{}: switch_number={}, switch_state_value={:01x}, switch_state={}{}{}>".\
            format(self.__class__.__name__,
                   str(self._switch_number),
                   self._switch_state_value,
                   str(self._switch_state),
                   '' if not self._was_set else ", was_set",
                   '' if not self._is_error else ", is_error")


class EventLogResponse(Response):
    """Response that provides an entry from the event log."""

    def __init__(self, text: str):
        Response.__init__(self)
        text = text[len(CMD_EVENT_LOG):]
        self._event_qualifier_value = from_ascii_hex(text[0:1])
        self._event_qualifier = ContactIDEventQualifier.parseint(self._event_qualifier_value)
        self._event_code_value = from_ascii_hex(text[1:4])
        self._event_code = ContactIDEventCode.parseint(self._event_code_value)
        group_partition = from_ascii_hex(text[4:6])
        # self._?? = from_ascii_hex(text[6:7])
        self._device_category = DC_ALL[from_ascii_hex(text[7:8])]
        zone_user = from_ascii_hex(text[8:10])
        if self._device_category == DC_BASEUNIT:
            self._group_number = None
            self._unit_number = None
            self._user_id = zone_user if zone_user != 0 else None
        else:
            self._group_number = group_partition
            self._unit_number = zone_user
            self._user_id = None
        self._action = DC_ALL[from_ascii_hex(text[10:12])]
        self._logged_date = text[12:14] + '/' + text[14:16]
        self._logged_time = datetime.strptime(
            text[16:18] + text[18:20], "%H%M").time()
        self._last_index = from_ascii_hex(text[20:23])

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
    def logged_time(self) -> time:
        """Time the event was logged."""
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
        return '{:02x}-{:02x}'.format(self._group_number, self._unit_number)

    def __repr__(self) -> str:
        zone_user = ''
        if self.zone is not None:
            zone_user = ", Zone '{}'".format(self.zone)
        elif self._user_id is not None:
            zone_user = ", User {:02x}".format(self._user_id)
        return "<{}: event_qualifier_value={:01x}, event_qualifier={}, " \
               "event_code_value={:03x}, event_code={}, device_category.description={}{}, " \
               "logged_date={}, logged_time={}>".format(
                   self.__class__.__name__,
                   self._event_qualifier_value,
                   str(self._event_qualifier),
                   self._event_code_value,
                   str(self._event_code),
                   self._device_category.description,
                   zone_user,
                   self._logged_date,
                   self._logged_time.strftime('%H:%M'))


class EventLogNotFoundResponse(Response):
    """Response that indicates there was no entry in event log at specified index."""

    def __init__(self, text: str):
        Response.__init__(self)

    @property
    def command_name(self) -> str:
        """Provides the command name."""
        return CMD_EVENT_LOG


class SensorLogResponse(Response):
    """Response that provides an entry from the Special sensor log."""

    def __init__(self, text: str):
        Response.__init__(self)
        text = text[len(CMD_SENSOR_LOG):]
        self._group_number = from_ascii_hex(text[0:2])
        self._unit_number = from_ascii_hex(text[2:4])
        self._logged_day = int(text[4:6])
        self._logged_time = datetime.strptime(
            text[6:8] + text[8:10], "%H%M").time()
        # I'm guessing the sensor log was created before the AC Power Meter,
        # since the message_attribute doesn't exist and the reading is always
        # assumed to be a signed byte.
        self._reading = decode_value_using_ma(MA_NONE, from_ascii_hex(text[10:12]))
        self._last_index = from_ascii_hex(text[12:15])

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
    def logged_day(self) -> int:
        """Day of month the event was logged."""
        return self._logged_day

    @property
    def logged_time(self) -> time:
        """Time the event was logged."""
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
        return "<{}: zone={}, reading={}, logged_day={}, logged_time={}>". \
            format(self.__class__.__name__,
                   self.zone,
                   self._reading,
                   self._logged_day,
                   self._logged_time.strftime('%H:%M'))


class SensorLogNotFoundResponse(Response):
    """Response that indicates there was no entry in Special sensor log at specified index."""

    def __init__(self, text: str):
        Response.__init__(self)

    @property
    def command_name(self) -> str:
        """Provides the command name."""
        return CMD_SENSOR_LOG
