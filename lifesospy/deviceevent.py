from lifesospy.enums import (
    DeviceType, DeviceEventCode as EventCode, DCFlags)
from lifesospy.util import *
from typing import Optional, Dict, Any


class DeviceEvent(object):
    """Represents a device event."""

    def __init__(self, text: str):
        if len(text) < 19:
            raise ValueError("Event length is invalid.")

        self._event_code_value = int(text[7:11], 16)
        self._event_code = EventCode.parseint(self._event_code_value)
        self._device_type_value = int(text[11:13], 16)
        self._device_type = DeviceType.parseint(self._device_type_value)
        self._device_id = int(text[13:19], 16)
        self._message_attribute = int(text[19:21], 16)
        self._device_characteristics = DCFlags(int(text[21:23], 16))
        self._current_status = int(text[23:25], 16)
        # I have a feeling the next two are provided by the base unit even
        # if the device didn't send them... given current_reading always
        # shows my last temperature sensor reading on any burglar device
        # events that follow it (ie. probably whatever was in buffer)
        #if len(text) > 25:
        #    self._?? = int(text[25:27], 16)
        if len(text) > 27:
            self._current_reading = decode_value_using_ma(
                self._message_attribute, int(text[27:29], 16))

    #
    # PROPERTIES
    #

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
        return "<{}: device_id={:06x}, device_type_value={:02x}, device_type={}, event_code_value={:04x}, event_code={}, rssi_db={}, device_characteristics={}, current_reading={}>".\
            format(self.__class__.__name__,
                   self._device_id,
                   self._device_type_value,
                   str(self._device_type),
                   self._event_code_value,
                   str(self._event_code),
                   self.rssi_db,
                   str(self._device_characteristics),
                   self._current_reading)

    def as_dict(self) -> Dict[str, Any]:
        """Converts to a dict of attributes for easier JSON serialisation."""
        return obj_to_dict(self)
