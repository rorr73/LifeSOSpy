import sys

from enum import Enum
if float('%s.%s' % sys.version_info[:2]) >= 3.6:
    from enum import IntFlag
else:
    from aenum import IntFlag
from lifesospy.const import *
from typing import Dict, Any, Optional, Union


def to_ascii_hex(value: int, digits: int) -> str:
    """Converts an int value to ASCII hex, as used by LifeSOS.
       Unlike regular hex, it uses the first 6 characters that follow
       numerics on the ASCII table instead of A - F."""
    if digits < 1:
        return ''
    text = ''
    for index in range(0, digits):
        text = chr(ord('0') + (value % 0x10)) + text
        value //= 0x10
    return text


def from_ascii_hex(text:str) -> int:
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


def is_ascii_hex(text:str) -> bool:
    """Indicates if specified text contains only ascii hex characters."""
    try:
        from_ascii_hex(text)
        return True
    except ValueError:
        return False


def obj_to_dict(obj: Any) -> Dict[str, Any]:
    """Converts to a dict of attributes for easier JSON serialisation."""
    from enum import IntEnum
    data = {}
    for name in dir(obj.__class__):
        if not isinstance(getattr(obj.__class__, name), property):
            continue
        value = getattr(obj, name)
        if hasattr(value, 'as_dict'):
            value = value.as_dict()
        elif isinstance(value, IntFlag):
            value = str(value)
            if value == '0':
                value = None
            else:
                value = value.split('|')
        elif isinstance(value, Enum):
            value = str(value)
        data[name] = value
    return data


def decode_value_using_ma(message_attribute: int, value: int) -> \
        Optional[Union[int, float]]:
    """Decode special sensor value using the message attribute."""
    if message_attribute == MA_TX3AC_100A:
        # TX-3AC in 100A mode; use value as-is, with 0xFE indicating null
        if value == 0xfe:
            return None
        else:
            return value
    elif message_attribute == MA_TX3AC_10A:
        # TX-3AC in 10A mode; shift decimal point, with 0xFE indicating null
        if value == 0xfe:
            return None
        else:
            return value / 10
    else:
        # Signed byte, with 0x80 indicating null
        if value == 0x80:
            return None
        elif value >= 0x80:
            return 0 - (0x100 - value)
        else:
            return value

def encode_value_using_ma(message_attribute: int, value: Optional[Union[int, float]]) -> int:
    """Encode special sensor value using the message attribute."""
    if message_attribute == MA_TX3AC_100A:
        # TX-3AC in 100A mode; use value as-is, with 0xFE indicating null
        if value is None:
            return 0xfe
        else:
            return int(value)
    elif message_attribute == MA_TX3AC_10A:
        # TX-3AC in 10A mode; shift decimal point, with 0xFE indicating null
        if value is None:
            return 0xfe
        else:
            return int(value * 10)
    else:
        # Signed byte, with 0x80 indicating null
        if value is None:
            return 0x80
        elif value < 0:
            return 0x100 + int(value)
        else:
            return int(value)
