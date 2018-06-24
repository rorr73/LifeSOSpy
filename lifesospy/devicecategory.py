from collections import OrderedDict
from lifesospy.util import *
from typing import Optional, Dict, Any


class DeviceCategory(object):
    """Represents a category of devices."""

    def __init__(self, id: str, description: str, max_devices: Optional[int]):
        self._id = id
        self._description = description
        self._max_devices = max_devices

    @property
    def id(self) -> str:
        """Identifier for the category.

        This is a single character that is used in device commands
        and is shown on the base unit when reporting events."""
        return self._id

    @property
    def description(self) -> str:
        """Description for the category."""
        return self._description

    @property
    def max_devices(self) -> int:
        """Maximum number of devices supported by this category."""
        return self._max_devices

    def __repr__(self) -> str:
        return "<DeviceCategory: Id '{}', Description '{}', Max Devices {}>".\
            format(self._id,
                   self._description,
                   self._max_devices)

    def as_dict(self) -> Dict[str, Any]:
        """Converts to a dict of attributes for easier JSON serialisation."""
        return obj_to_dict(self)


# Device categories
DC_CONTROLLER = DeviceCategory('c', 'Controller', 32)
DC_BURGLAR = DeviceCategory('b', 'Burglar', 128)
DC_FIRE = DeviceCategory('f', 'Fire', 64)
DC_MEDICAL = DeviceCategory('m', 'Medical', 32)
DC_SPECIAL = DeviceCategory('e', 'Special', 32)
DC_BASEUNIT = DeviceCategory('z', 'Base Unit', None)
DC_ALL = [
    DC_CONTROLLER, DC_BURGLAR, DC_FIRE, DC_MEDICAL, DC_SPECIAL, DC_BASEUNIT]
DC_ALL_LOOKUP = OrderedDict()
for dc in DC_ALL:
    DC_ALL_LOOKUP[dc.id] = dc
