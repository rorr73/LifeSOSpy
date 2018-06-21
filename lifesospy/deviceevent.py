from lifesospy.enums import (
    DeviceType, DeviceEventCode as EventCode, DCFlags)
from typing import Optional


class DeviceEvent(object):
    """Represents a device event."""

    def __init__(self, text: str):
        if len(text) < 19:
            raise ValueError("Event length is invalid.")

        self._event_code_value = int(text[7:11], 16)
        self._device_type_value = int(text[11:13], 16)
        self._device_id = int(text[13:19], 16)
        self._message_attribute = int(text[19:21], 16)
        self._device_characteristics = DCFlags(int(text[21:23], 16))
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

    #
    # PROPERTIES
    #

    @property
    def current_status(self) -> int:
        """Multi-purpose field containing RSSI reading and magnet sensor flag.
           Recommend using the 'rssi_db', 'rssi_bars' or 'is_closed' properties
           instead. """
        return self._current_status

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
    def event_code(self) -> Optional[EventCode]:
        """Type of event."""
        return self._event_code

    @property
    def event_code_value(self) -> int:
        """Value that represents the type of event."""
        return self._event_code_value

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

    #
    # METHODS - Public
    #

    def __repr__(self) -> str:
        return "<DeviceEvent: Id {:06x}, Type {:02x} ({}), Event {:04x} ({}), RSSI {} dB, {}>".\
            format(self._device_id,
                   self._device_type_value,
                   "Unknown" if not self._device_type else self._device_type.name,
                   self._event_code_value,
                   "Unknown" if not self._event_code else self._event_code.name,
                   self.rssi_db,
                   str(self._device_characteristics))
