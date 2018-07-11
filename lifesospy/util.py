"""
This module contains utility functions used by various classes and modules.
"""

import sys

from collections.abc import Container, Iterable # pylint: disable=unused-import
from typing import Any, Optional, Union, Callable
from enum import Enum
from lifesospy.const import MA_TX3AC_100A, MA_TX3AC_10A
if float('%s.%s' % sys.version_info[:2]) >= 3.6:
    from enum import IntFlag # pylint: disable=no-name-in-module
else:
    from aenum import IntFlag


def to_ascii_hex(value: int, digits: int) -> str:
    """Converts an int value to ASCII hex, as used by LifeSOS.
       Unlike regular hex, it uses the first 6 characters that follow
       numerics on the ASCII table instead of A - F."""
    if digits < 1:
        return ''
    text = ''
    for _ in range(0, digits):
        text = chr(ord('0') + (value % 0x10)) + text
        value //= 0x10
    return text


def from_ascii_hex(text: str) -> int:
    """Converts to an int value from both ASCII and regular hex.
       The format used appears to vary based on whether the command was to
       get an existing value (regular hex) or set a new value (ASCII hex
       mirrored back from original command).

       Regular hex: 0123456789abcdef
       ASCII hex:   0123456789:;<=>?  """
    value = 0
    for index in range(0, len(text)):
        char_ord = ord(text[index:index + 1])
        if char_ord in range(ord('0'), ord('?') + 1):
            digit = char_ord - ord('0')
        elif char_ord in range(ord('a'), ord('f') + 1):
            digit = 0xa + (char_ord - ord('a'))
        else:
            raise ValueError(
                "Response contains invalid character.")
        value = (value * 0x10) + digit
    return value


def is_ascii_hex(text: str) -> bool:
    """Indicates if specified text contains only ascii hex characters."""
    try:
        from_ascii_hex(text)
        return True
    except ValueError:
        return False


def serializable(obj: Any, on_filter: Callable[[Any, str], bool] = None) -> Any:
    """
    Ensures the specified object is serializable, converting if necessary.

    :param obj: the object to use.
    :param on_filter: optional function that can be used to filter which
                      properties on the object will be included.
    :return value representing the object, which is serializable.
    """

    # Will be called recursively when object has children
    def _serializable(parent_obj: Any, obj: Any,
                      on_filter: Callable[[Any, str], bool]) -> Any:
        # None can be left as-is
        if obj is None:
            return obj

        # IntFlag enums should be broken down to a list of names
        elif isinstance(obj, IntFlag):
            value = str(obj)
            if value == '0':
                return None
            return value.split('|')

        # Any other enum just use the name
        elif isinstance(obj, Enum):
            return str(obj)

        # Simple types can be left as-is
        elif isinstance(obj, (bool, int, float, str)):
            return obj

        # Class supports method to convert to serializable dictionary; use it
        elif hasattr(obj, 'as_dict') and parent_obj is not None:
            return obj.as_dict()

        elif isinstance(obj, dict):
            # Dictionaries will require us to check each key and value
            new_dict = {}
            for item in obj.items():
                new_dict[_serializable(obj, item[0], on_filter=on_filter)] = \
                    _serializable(obj, item[1], on_filter=on_filter)
            return new_dict

        elif isinstance(obj, (list, Container)):
            # Lists will require us to check each item
            items = obj # type: Iterable
            new_list = []
            for item in items:
                new_list.append(_serializable(obj, item, on_filter=on_filter))
            return new_list

        # Convert to a dictionary of property name/values
        data = {}
        for name in dir(obj.__class__):
            if not isinstance(getattr(obj.__class__, name), property):
                continue
            elif on_filter and not on_filter(obj, name):
                continue
            value = getattr(obj, name)
            data[name] = _serializable(obj, value, on_filter=on_filter)
        return data

    return _serializable(None, obj, on_filter)


def decode_value_using_ma(message_attribute: int, value: int) -> \
        Optional[Union[int, float]]:
    """Decode special sensor value using the message attribute."""
    if message_attribute == MA_TX3AC_100A:
        # TX-3AC in 100A mode; use value as-is, with 0xFE indicating null
        if value == 0xfe:
            return None
        return value
    elif message_attribute == MA_TX3AC_10A:
        # TX-3AC in 10A mode; shift decimal point, with 0xFE indicating null
        if value == 0xfe:
            return None
        return value / 10
    else:
        # Signed byte, with 0x80 indicating null
        if value == 0x80:
            return None
        elif value >= 0x80:
            return 0 - (0x100 - value)
        return value


def encode_value_using_ma(message_attribute: int, value: Optional[Union[int, float]]) -> int:
    """Encode special sensor value using the message attribute."""
    if message_attribute == MA_TX3AC_100A:
        # TX-3AC in 100A mode; use value as-is, with 0xFE indicating null
        if value is None:
            return 0xfe
        return int(value)
    elif message_attribute == MA_TX3AC_10A:
        # TX-3AC in 10A mode; shift decimal point, with 0xFE indicating null
        if value is None:
            return 0xfe
        return int(value * 10)
    else:
        # Signed byte, with 0x80 indicating null
        if value is None:
            return 0x80
        elif value < 0:
            return 0x100 + int(value)
        return int(value)
