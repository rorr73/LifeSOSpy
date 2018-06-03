from lifesospy.enums import *

class DeviceEvent(object):
    """Represents a device event."""

    def __init__(self, text):
        if len(text) < 19:
            raise ValueError("Event length is invalid.")

        self._event_code_value = int(text[7:11], 16)
        self._device_type_value = int(text[11:13], 16)
        self._device_id = int(text[13:19], 16)
        self._ma = int(text[19:21], 16)
        self._device_char = DCFlags(int(text[21:23], 16))
        self._current_status = int(text[23:25], 16)
        # self._?? = int(text[25:27], 16)
        # self._?? = int(text[27:29], 16)

        if EventCode.has_value(self._event_code_value):
            self._event_code = EventCode(self._event_code_value)
        else:
            self._event_code = None

        if DeviceType.has_value(self._device_type_value):
            self._device_type = DeviceType(self._device_type_value)
        else:
            self._device_type = None

    @property
    def event_code_value(self):
        """Value that represents the type of event."""
        return self._event_code_value

    @property
    def event_code(self):
        """Type of event."""
        return self._event_code

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

    def __str__(self):
        return "Device Id {0:06x}, Type {1:02x} ({2}), Event {3:04x} ({4}), RSSI {5} dB{6}, {7}.".\
            format(self._device_id,
                   self._device_type_value,
                   "Unknown" if not self._device_type else self._device_type.name,
                   self._event_code_value,
                   "Unknown" if not self._event_code else self._event_code.name,
                   self.rssi_db,
                   '' if self._device_type_value != DeviceType.DoorMagnet else ", IsClosed={0}".format(
                       self.is_closed),
                   str(self._device_char))
