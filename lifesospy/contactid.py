from lifesospy.const import *
from lifesospy.enums import (
    ContactIDEventQualifier as EventQualifier,
    ContactIDEventCode as EventCode)

class ContactID(object):
    """Represents a message using the Ademco ® Contact ID protocol."""

    def __init__(self, text):
        if len(text) != 16:
            raise ValueError("ContactID message length is invalid.")

        # Verify checksum
        check_val = 0
        for c in text:
            check_digit = int(c, 16)
            check_val += (check_digit if not check_digit == 0 else 10)
        if check_val % 15 != 0:
            raise ValueError("ContactID message checksum failure.")

        self._account_number = int(text[0:4], 16)
        self._message_type = int(text[4:6], 16)
        if not self._message_type in [0x18, 0x98]:
            raise ValueError("ContactID message type is invalid.")
        self._event_qualifier_value = int(text[6:7], 16)
        self._event_code_value = int(text[7:10], 16)
        self._partition = int(text[10:12], 16)
        # Spec says zone/user uses next 3 digits, but LifeSOS only needs
        # 2 digits, so it seems to use first digit for device category index
        self._device_category = DC_ALL[int(text[12:13], 16)]
        self._zone_user = int(text[13:15], 16)
        self._checksum = int(text[15:16], 16)

        if EventQualifier.has_value(self._event_qualifier_value):
            self._event_qualifier = EventQualifier(self._event_qualifier_value)
        else:
            self._event_qualifier = None

        if EventCode.has_value(self._event_code_value):
            self._event_code = EventCode(self._event_code_value)
        else:
            self._event_code = None

    @property
    def account_number(self):
        return self._account_number

    @property
    def message_type(self):
        return self._message_type

    @property
    def event_qualifier_value(self):
        return self._event_qualifier_value

    @property
    def event_qualifier(self):
        return self._event_qualifier

    @property
    def event_code_value(self):
        return self._event_code_value

    @property
    def event_code(self):
        return self._event_code

    def device_category(self):
        return self._device_category

    @property
    def partition(self):
        return self._partition

    @property
    def zone_user(self):
        return self._zone_user

    @property
    def checksum(self):
        return self._checksum

    def __str__(self):
        return "Account {0:04x}, {1} {2:03x} ({3}), Category '{4}', Partition {5:02x}, {6} {7:02x}".\
            format(self._account_number,
                   self._event_qualifier_value if not self._event_qualifier else self._event_qualifier.name,
                   self._event_code_value,
                   "Unknown" if not self._event_code else self._event_code.name,
                   self._device_category.description,
                   self._partition,
                   "Zone" if self._device_category != DC_BASEUNIT else "User",
                   self._zone_user)

