"""
This module contains the PropertyChangedInfo class.
"""

from typing import Any, Dict
from lifesospy.util import obj_to_dict


class PropertyChangedInfo(object):
    """Provides details for a property change."""

    def __init__(self, name: str, old_value: Any, new_value: Any):
        self._name = name
        self._old_value = old_value
        self._new_value = new_value

    #
    # PROPERTIES
    #

    @property
    def name(self) -> str:
        """Name of the property that was changed."""
        return self._name

    @property
    def new_value(self) -> Any:
        """The new property value."""
        return self._new_value

    @property
    def old_value(self) -> Any:
        """The old property value."""
        return self._old_value

    #
    # METHODS - Public
    #

    def __repr__(self) -> str:
        return "<{}: name={}, old_value={}, new_value={}>".\
            format(self.__class__.__name__,
                   self._name,
                   str(self._old_value),
                   str(self._new_value))

    def as_dict(self) -> Dict[str, Any]:
        """Converts to a dict of attributes for easier JSON serialisation."""
        return obj_to_dict(self)
