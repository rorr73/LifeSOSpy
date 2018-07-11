"""
This module contains the ContactID class.
"""

from typing import Dict, Any, Optional
from lifesospy.devicecategory import DeviceCategory, DC_ALL, DC_BASEUNIT
from lifesospy.enums import (
    ContactIDEventQualifier as EventQualifier,
    ContactIDEventCategory as EventCategory,
    ContactIDEventCode as EventCode)
from lifesospy.util import serializable


class ContactID(object):
    """Represents a message using the Ademco ® Contact ID protocol."""

    def __init__(self, text: str):
        if len(text) != 16:
            raise ValueError("ContactID message length is invalid.")

        # Verify checksum
        check_val = 0
        for hexchar in text:
            check_digit = int(hexchar, 16)
            check_val += (check_digit if check_digit != 0 else 10)
        if check_val % 15 != 0:
            raise ValueError("ContactID message checksum failure.")

        self._account_number = int(text[0:4], 16)
        self._message_type = int(text[4:6], 16)
        if self._message_type not in [0x18, 0x98]:
            raise ValueError("ContactID message type is invalid.")
        self._event_qualifier_value = int(text[6:7], 16)
        self._event_qualifier = EventQualifier.parse_value(self._event_qualifier_value)
        self._event_code_value = int(text[7:10], 16)
        self._event_code = EventCode.parse_value(self._event_code_value)
        group_partition = int(text[10:12], 16)
        # Spec says zone/user uses next 3 digits; however LifeSOS uses the
        # first digit for device category index, and the remaining two digits
        # for either unit number or user id (depending on whether event is
        # for the base unit or not)
        self._device_category = DC_ALL[int(text[12:13], 16)]
        zone_user = int(text[13:15], 16)
        if self._device_category == DC_BASEUNIT:
            self._group_number = None
            self._unit_number = None
            self._user_id = zone_user if zone_user != 0 else None
        else:
            self._group_number = group_partition
            self._unit_number = zone_user
            self._user_id = None
        self._checksum = int(text[15:16], 16)

    #
    # PROPERTIES
    #

    @property
    def account_number(self) -> int:
        """Account number identifies this alarm panel to the receiver."""
        return self._account_number

    @property
    def checksum(self) -> int:
        """Checksum digit used to verify message integrity."""
        return self._checksum

    @property
    def device_category(self) -> DeviceCategory:
        """Category for the device."""
        return self._device_category

    @property
    def event_category(self) -> EventCategory:
        """Category for the type of event."""
        return EventCategory(self._event_code_value & 0xf00)

    @property
    def event_code(self) -> Optional[EventCode]:
        """Type of event."""
        return self._event_code

    @property
    def event_code_value(self) -> int:
        """Value that represents the type of event."""
        return self._event_code_value

    @property
    def event_qualifier(self) -> Optional[EventQualifier]:
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
    def message_type(self) -> int:
        """
        Message type is used to identify the message to the receiver.

        It must be 0x18 (preferred) or 0x98 (optional).
        """
        return self._message_type

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

    #
    # METHODS - Public
    #

    def __repr__(self) -> str:
        zone_user = ''
        if self.zone is not None:
            zone_user = ", Zone '{}'".format(self.zone)
        elif self._user_id is not None:
            zone_user = ", User {:02x}".format(self._user_id)
        return "<{}: account_number={:04x}, event_qualifier_value={:01x}, " \
               "event_qualifier={}, event_code_value={:03x}, event_code={}, " \
               "device_category.description={}{}>".format(
                   self.__class__.__name__,
                   self._account_number,
                   self._event_qualifier_value,
                   str(self._event_qualifier),
                   self._event_code_value,
                   str(self._event_code),
                   self._device_category.description,
                   zone_user)

    def as_dict(self) -> Dict[str, Any]:
        """Converts to a dict of attributes for easier serialization."""
        return serializable(self)
