from abc import ABC, abstractmethod
from datetime import datetime
from lifesospy.const import *
from lifesospy.enums import *

class Response(ABC):
    """Represents response from a command issued to the LifeSOS base unit."""

    def __init__(self, text):
        self._text = text

    @property
    @abstractmethod
    def command_name(self):
        """Provides the command name."""
        return ''

    @property
    def text(self):
        """The original (undecoded) response text."""
        return self._text

    @staticmethod
    def parse(text):
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
            if text[2:4] == 'no' or text[2:4] == '00':
                return DeviceNotFoundResponse(text)
            else:
                return DeviceInfoResponse(text)

        elif text.startswith(CMD_DEVBYZON_PREFIX):
            if text[2:4] == 'no':
                return DeviceNotFoundResponse(text)
            else:
                return DeviceInfoResponse(text)

        elif text.startswith(CMD_CLEAR_STATUS):
            return ClearedStatusResponse(text)

        elif text.startswith(CMD_ROMVER):
            return ROMVersionResponse(text)

        elif text.startswith(CMD_EXIT_DELAY):
            return ExitDelayResponse(text)

        else:
            raise ValueError("Response not recognised: " + text)

    def _from_ascii_hex(self, text):
        """Converts to an int value from both ASCII and regular hex.
           The format used appears to vary based on whether the command was to
           get an existing value (regular hex) or set a new value (ASCII hex
           mirrored back from original command).

           Regular hex: 0123456789abcdef
           ASCII hex:   0123456789:;<=>?  """
        value = 0
        for index in range(0, len(text)):
            char_ord = ord(text[index:index+1])
            if char_ord in range(ord('0'), ord('?') + 1):
                digit = char_ord - ord('0')
            elif char_ord in range(ord('a'), ord('f') + 1):
                digit = 0xa + (char_ord - ord('a'))
            else:
                raise ValueError(
                    "Response contains invalid character.")
            value = (value * 0x10) + digit
        return value

class DateTimeResponse(Response):
    """Response that provides the current date/time on the LifeSOS base unit."""

    def __init__(self, text):
        super().__init__(text)
        text = text[len(CMD_DATETIME):]
        self._was_set = text.startswith(ACTION_SET)
        if self._was_set:
            text = text[1:]
        if len(text) != 11:
            raise ValueError("Date/Time response length is invalid.")
        self._remote_datetime = datetime.strptime(text, '%y%m%d%w%H%M')

    @property
    def command_name(self):
        return CMD_DATETIME

    @property
    def remote_datetime(self):
        """Date/Time on the LifeSOS base unit."""
        return self._remote_datetime

    @property
    def was_set(self):
        """True if date/time was set on the base unit; otherwise, False."""
        return self._was_set

    def __str__(self):
        return "Remote date/time {0} {1}.".\
            format('is' if not self._was_set else "was set to",
                   self._remote_datetime.strftime('%a %d %b %Y %I:%M %p'))

class OpModeResponse(Response):
    """Response that provides the current operation mode on the LifeSOS base unit."""

    def __init__(self, text):
        super().__init__(text)
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
    def command_name(self):
        return CMD_OPMODE

    @property
    def operation_mode(self):
        """Operation mode on the LifeSOS base unit."""
        return self._operation_mode

    @property
    def was_set(self):
        """True if operation mode was set on the base unit; otherwise, False."""
        return self._was_set

    def __str__(self):
        return "Operation mode {0} {1:x} ({2}).".\
            format('is' if not self._was_set else "was set to",
                   self._operation_mode_value,
                   'Unknown' if self._operation_mode is None else self._operation_mode.name)

class DeviceInfoResponse(Response):
    """Response that provides information for one of the LifeSOS devices."""

    def __init__(self, text):
        super().__init__(text)
        self._command_name = text[0:2]
        self._device_category = DC_ALL_LOOKUP[text[1:2]]
        text = text[2:]
        if self._command_name.startswith(CMD_DEVBYZON_PREFIX):
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
        self._ma = int(text[8:10], 16)
        self._device_char = DCFlags(int(text[10:12], 16))
        # self._?? = int(text[12:14], 16)
        self._group_number = int(text[14:16], 16)
        self._unit_number = int(text[16:18], 16)
        self._enable_status = ESFlags(int(text[18:22], 16))
        self._switches = int(text[22:26], 16)
        self._current_status = int(text[26:28], 16)
        self._down_count = int(text[28:30], 16)

        # Remaining fields used by the 'Special' category of devices
        if len(text) > 30:
            self._current_reading = int(text[30:32], 16)
            self._alarm_high_limit = int(text[32:34], 16)
            self._alarm_low_limit = int(text[34:36], 16)
            self._special_status = SSFlags(int(text[36:38], 16))
        else:
            self._current_reading = None
            self._alarm_high_limit = None
            self._alarm_low_limit = None
            self._special_status = None
        if len(text) > 38:
            self._control_high_limit = int(text[38:40], 16)
            self._control_low_limit = int(text[40:42], 16)
        else:
            self._control_high_limit = None
            self._control_low_limit = None

    @property
    def command_name(self):
        return self._command_name

    @property
    def device_category(self):
        """Category for the device."""
        return self._device_category

    @property
    def index(self):
        """Index of device within the category.
           Only provided in response to a GetDeviceByZone command."""
        return self._index

    @property
    def device_type_value(self):
        """Value that represents the type of device."""
        return self._device_type_value

    @property
    def device_type(self):
        """Type of device."""
        return self._device_type

    @property
    def device_id(self):
        """Unique identifier for the device."""
        return self._device_id

    @property
    def ma(self):
        """For AC Power Meter; 01 for 10 Amp range, 02 for 100 Amp range."""
        return self._ma

    @property
    def device_char(self):
        """Device Characteristics flags."""
        return self._device_char

    @property
    def group_number(self):
        """Group number the device is assigned to."""
        return self._group_number

    @property
    def unit_number(self):
        """Unit number the device is assigned to (within group)."""
        return self._unit_number

    @property
    def zone(self):
        return '{0:02x}-{1:02x}'.format(self._group_number, self._unit_number)

    @property
    def enable_status(self):
        """Enable Status flags."""
        return self._enable_status

    @property
    def switches(self):
        """Indicates if switches SW1-SW16 will be triggered by device.
           These are bit flags; 0x8000 for SW1 through to 0x0001 for SW16."""
        return self._switches

    @property
    def current_status(self):
        """Multi-purpose field containing RSSI reading and magnet sensor flag.
           Recommend using the 'rssi_db', 'rssi_bars' or 'is_closed' properties
           instead. """
        return self._current_status

    @property
    def rssi_db(self):
        """Received Signal Strength Indication, in dB."""
        return max(min(self._current_status - 0x40, 99), 0)

    @property
    def rssi_bars(self):
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
    def is_closed(self):
        """For Magnet Sensor; True if Closed, False if Open."""
        return bool(self._current_status & 0x01)

    @property
    def down_count(self):
        """Supervisory down count timer.
           When this reaches zero, a 'Loss of Supervision-RF' event is raised."""
        return self._down_count

    @property
    def current_reading(self):
        """Current reading data."""
        return self._current_reading

    @property
    def alarm_high_limit(self):
        """Alarm high limit setting."""
        return self._alarm_high_limit

    @property
    def alarm_low_limit(self):
        """Alarm low limit setting."""
        return self._alarm_low_limit

    @property
    def special_status(self):
        """Special sensor status flags."""
        return self._special_status

    @property
    def control_high_limit(self):
        """Control high limit setting."""
        return self._control_high_limit

    @property
    def control_low_limit(self):
        """Control low limit setting."""
        return self._control_low_limit

    def __str__(self):
        return "Device Info: Id {0:06x}, Type {1:02x} ({2}), Category '{3}', Zone '{4}', RSSI {5} dB{6}, {7}, {8}.".\
            format(self._device_id,
                   self._device_type_value,
                   'Unknown' if self._device_type is None else self._device_type.name,
                   self._device_category.description,
                   self.zone,
                   self.rssi_db,
                   '' if self._device_type_value != DeviceType.DoorMagnet else ", IsClosed={0}".format(self.is_closed),
                   str(self._device_char),
                   str(self._enable_status))

class DeviceNotFoundResponse(Response):
    """Response that indicates there was no device at specified index or zone."""

    def __init__(self, text):
        super().__init__(text)
        self._command_name = text[0:2]
        self._device_category = DC_ALL_LOOKUP[text[1:2]]

    @property
    def command_name(self):
        return self._command_name

    @property
    def device_category(self):
        """Category for the device."""
        return self._device_category

    def __str__(self):
        return "Device Not Found: Get '{0}', Category '{1}'.".\
            format("By Index" if self._command_name.startswith(CMD_DEVBYIDX_PREFIX) else "By Zone",
                   self._device_category.description)

class ClearedStatusResponse(Response):
    """Response that indicates status was cleared on base unit."""

    def __init__(self, text):
        super().__init__(text)

    @property
    def command_name(self):
        return CMD_CLEAR_STATUS

    def __str__(self):
        return "Cleared status on base unit."

class ROMVersionResponse(Response):
    """Response that provides the ROM version on the base unit."""

    def __init__(self, text):
        super().__init__(text)
        text = text[len(CMD_ROMVER):]
        self._version = text

    @property
    def command_name(self):
        return CMD_ROMVER

    @property
    def version(self):
        """ROM version string."""
        return self._version

    def __str__(self):
        return "ROM version is '{0}'.".format(self._version)

class ExitDelayResponse(Response):
    """Response that provides the current exit delay on the LifeSOS base unit."""

    def __init__(self, text):
        super().__init__(text)
        text = text[len(CMD_EXIT_DELAY):]
        self._was_set = text.startswith(ACTION_SET)
        if self._was_set:
            text = text[1:]
        self._exit_delay = self._from_ascii_hex(text)

    @property
    def command_name(self):
        return CMD_EXIT_DELAY

    @property
    def exit_delay(self):
        """Exit delay (in seconds) on the LifeSOS base unit."""
        return self._exit_delay

    @property
    def was_set(self):
        """True if exit delay was set on the base unit; otherwise, False."""
        return self._was_set

    def __str__(self):
        return "Exit delay {0} {1} seconds.".\
            format('is' if not self._was_set else "was set to",
                   self._exit_delay)
