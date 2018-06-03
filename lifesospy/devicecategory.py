class DeviceCategory(object):
    """Represents a category of devices."""

    def __init__(self, id, description, max_devices):
        self._id = id
        self._description = description
        self._max_devices = max_devices

    @property
    def id(self):
        """Identifier for the category.

        This is a single character that is used in device commands
        and is shown on the base unit when reporting events."""
        return self._id

    @property
    def description(self):
        """Description for the category."""
        return self._description

    @property
    def max_devices(self):
        """Maximum number of devices supported by this category."""
        return self._max_devices

    def __str__(self):
        return "Id '{0}', Description '{1}', Max Devices {2}".\
            format(self._id,
                   self._description,
                   self._max_devices)
