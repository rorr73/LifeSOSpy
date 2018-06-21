from typing import Any


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
        return "<PropertyChangedInfo: '{}' changed from {} to {}>".\
            format(self._name,
                   "Unknown" if self._old_value is None else str(self._old_value),
                   "Unknown" if self._new_value is None else str(self._new_value))
