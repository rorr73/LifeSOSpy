def to_ascii_hex(value, digits):
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

def from_ascii_hex(text):
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
