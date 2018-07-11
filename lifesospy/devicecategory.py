"""
This module provides the DeviceCategory class that contains all details for
a device category, and declares fixed instances of each available device
category supported by the base unit.
"""

from collections import OrderedDict
from typing import Optional, Dict, Any
from lifesospy.util import serializable


class DeviceCategory(object):
    """Represents a category of devices."""

    def __init__(self, code: str, description: str, max_devices: Optional[int]):
        self._code = code
        self._description = description
        self._max_devices = max_devices

    @property
    def code(self) -> str:
        """Code that identifies this category.

        This is a single character that is used in device commands
        and is shown on the base unit when reporting events."""
        return self._code

    @property
    def description(self) -> str:
        """Description for the category."""
        return self._description

    @property
    def max_devices(self) -> int:
        """Maximum number of devices supported by this category."""
        return self._max_devices

    def __repr__(self) -> str:
        return "<{}: code={}, description={}, max_devices={}>".\
            format(self.__class__.__name__,
                   self._code,
                   self._description,
                   self._max_devices)

    def as_dict(self) -> Dict[str, Any]:
        """Converts to a dict of attributes for easier serialization."""
        return serializable(self)


# Device categories
DC_CONTROLLER = DeviceCategory('c', 'Controller', 32)
DC_BURGLAR = DeviceCategory('b', 'Burglar', 128)
DC_FIRE = DeviceCategory('f', 'Fire', 64)
DC_MEDICAL = DeviceCategory('m', 'Medical', 32)
DC_SPECIAL = DeviceCategory('e', 'Special', 32)
DC_BASEUNIT = DeviceCategory('z', 'Base Unit', None)

# List of all device categories
# Note: Order is important, as the index is referenced by some responses.
DC_ALL = [DC_CONTROLLER, DC_BURGLAR, DC_FIRE, DC_MEDICAL, DC_SPECIAL, DC_BASEUNIT]

# Dictionary of all device categories, for lookup using the code
DC_ALL_LOOKUP = OrderedDict()
for dc in DC_ALL:
    DC_ALL_LOOKUP[dc.code] = dc
