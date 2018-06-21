import logging

from collections.abc import Sized, Iterable, Container
from lifesospy.devicecategory import *
from lifesospy.deviceevent import DeviceEvent
from lifesospy.enums import (
    DeviceType, DCFlags, ESFlags, SSFlags, DeviceEventCode, SwitchFlags)
from lifesospy.propertychangedinfo import PropertyChangedInfo
from lifesospy.response import DeviceInfoResponse, DeviceSettingsResponse
from typing import (
    Callable, Dict, List, Any, Optional, Union, Iterator, overload)

_LOGGER = logging.getLogger(__name__)


class Device(object):
    """
    Represents a device that has been enrolled on the base unit.
    """

    # Property names
    PROP_ALARM_HIGH_LIMIT = 'alarm_high_limit'
    PROP_ALARM_LOW_LIMIT = 'alarm_low_limit'
    PROP_CATEGORY = 'category'
    PROP_CHARACTERISTICS = 'characteristics'
    PROP_CONTROL_HIGH_LIMIT = 'control_high_limit'
    PROP_CONTROL_LOW_LIMIT = 'control_low_limit'
    PROP_CURRENT_READING = 'current_reading'
    PROP_ENABLE_STATUS = 'enable_status'
    PROP_GROUP_NUMBER = 'group_number'
    PROP_ID = 'id'
    PROP_IS_CLOSED = 'is_closed'
    PROP_RSSI_BARS = 'rssi_bars'
    PROP_RSSI_DB = 'rssi_db'
    PROP_SPECIAL_STATUS = 'special_status'
    PROP_SWITCHES = 'switches'
    PROP_TYPE = 'type'
    PROP_TYPE_VALUE = 'type_value'
    PROP_UNIT_NUMBER = 'unit_number'
    PROP_ZONE = 'zone'

    def __init__(self, response: DeviceInfoResponse):
        self._on_event = None
        self._on_properties_changed = None

        # Init fixed and variable property values
        self._notify_properties_changed = False
        self._set_field_values({
            Device.PROP_ID: response.device_id,
            Device.PROP_CATEGORY: response.device_category,
            Device.PROP_TYPE_VALUE: response.device_type_value,
            Device.PROP_TYPE: response.device_type,
            Device.PROP_CHARACTERISTICS: response.device_characteristics
        })
        self._handle_response(response)
        self._notify_properties_changed = True

    #
    # PROPERTIES
    #

    @property
    def alarm_high_limit(self) -> Optional[int]:
        """Alarm high limit setting for a special sensor."""
        return self._get_field_value(Device.PROP_ALARM_HIGH_LIMIT)

    @property
    def alarm_low_limit(self) -> Optional[int]:
        """Alarm low limit setting for a special sensor."""
        return self._get_field_value(Device.PROP_ALARM_LOW_LIMIT)

    @property
    def category(self) -> DeviceCategory:
        """Category for the device."""
        return self._get_field_value(Device.PROP_CATEGORY)

    @property
    def characteristics(self) -> DCFlags:
        """Flags indicating the device characteristics."""
        return self._get_field_value(Device.PROP_CHARACTERISTICS)

    @property
    def control_high_limit(self) -> Optional[int]:
        """Control high limit setting for a special sensor."""
        return self._get_field_value(Device.PROP_CONTROL_HIGH_LIMIT)

    @property
    def control_low_limit(self) -> Optional[int]:
        """Control low limit setting for a special sensor."""
        return self._get_field_value(Device.PROP_CONTROL_LOW_LIMIT)

    @property
    def current_reading(self) -> Optional[int]:
        """Current reading for a special sensor."""
        return self._get_field_value(Device.PROP_CURRENT_READING)

    @property
    def enable_status(self) -> ESFlags:
        """Flags indicating settings that have been enabled."""
        return self._get_field_value(Device.PROP_ENABLE_STATUS)

    @property
    def group_number(self) -> int:
        """Group number the device is assigned to."""
        return self._get_field_value(Device.PROP_GROUP_NUMBER)

    @property
    def id(self) -> int:
        """Unique identifier for the device."""
        return self._get_field_value(Device.PROP_ID)

    @property
    def is_closed(self) -> Optional[bool]:
        """For Magnet Sensor; True if Closed, False if Open."""
        return self._get_field_value(Device.PROP_IS_CLOSED)

    @property
    def rssi_bars(self) -> int:
        """Received Signal Strength Indication, from 0 to 4 bars."""
        return self._get_field_value(Device.PROP_RSSI_BARS)

    @property
    def rssi_db(self) -> int:
        """Received Signal Strength Indication, in dB."""
        return self._get_field_value(Device.PROP_RSSI_DB)

    @property
    def special_status(self) -> Optional[SSFlags]:
        """Special sensor status flags."""
        return self._get_field_value(Device.PROP_SPECIAL_STATUS)

    @property
    def switches(self) -> Optional[SwitchFlags]:
        """Indicates switches that will be activated when device is triggered."""
        return self._get_field_value(Device.PROP_SWITCHES)

    @property
    def type(self) -> Optional[DeviceType]:
        """Type of device."""
        return self._get_field_value(Device.PROP_TYPE)

    @property
    def type_value(self) -> int:
        """Value that represents the type of device."""
        return self._get_field_value(Device.PROP_TYPE_VALUE)

    @property
    def unit_number(self) -> int:
        """Unit number the device is assigned to (within group)."""
        return self._get_field_value(Device.PROP_UNIT_NUMBER)

    @property
    def zone(self) -> str:
        """Zone the device is assigned to."""
        return self._get_field_value(Device.PROP_ZONE)

    #
    # EVENTS
    #

    @property
    def on_event(self) -> Callable[['Device', DeviceEventCode], None]:
        """If implemented, called when an event occurs."""
        return self._on_event

    @on_event.setter
    def on_event(self, func: Callable[['Device', DeviceEventCode], None]):
        """
        Define the event callback implementation.

        Expected signature is:
            event_callback(device, event_code)

        device:         the device instance for this callback
        event_code:     the type of event.
        """
        self._on_event = func

    @property
    def on_properties_changed(self) -> Callable[['Device', List[PropertyChangedInfo]], None]:
        """If implemented, called after property values have been changed."""
        return self._on_properties_changed

    @on_properties_changed.setter
    def on_properties_changed(self, func: Callable[['Device', List[PropertyChangedInfo]], None]):
        """
        Define the properties changed callback implementation.

        Expected signature is:
            properties_changed_callback(device, dict)

        device:         the device instance for this callback
        changes:        list providing name and values of changed properties
        """
        self._on_properties_changed = func

    #
    # METHODS - Public
    #

    def __repr__(self) -> str:
        """Provides an info string for the device."""
        return "<Device: Id {:06x}, Type {:02x} ({}), Category '{}', Zone '{}', RSSI {} dB{}, {}, {}, {}>".\
            format(self.id,
                   self.type_value,
                   'Unknown' if self.type is None else self.type.name,
                   self.category.description,
                   self.zone,
                   self.rssi_db,
                   '' if self.type_value != DeviceType.DoorMagnet else ", IsClosed={}".format(self.is_closed),
                   str(self.characteristics),
                   str(self.enable_status),
                   str(self.switches))

    #
    # METHODS - Private / Internal
    #

    def _handle_device_event(self, device_event: DeviceEvent):
        # Magnet sensor open/close state only exists in device info response;
        # for device events, we should update based on the event Open/Close
        is_closed = self.is_closed
        if device_event.event_code is not None:
            if device_event.event_code == DeviceEventCode.Open:
                is_closed = False
            elif device_event.event_code == DeviceEventCode.Close:
                is_closed = True

        # Update properties
        self._set_field_values({
            Device.PROP_IS_CLOSED: is_closed,
            Device.PROP_RSSI_BARS: device_event.rssi_bars,
            Device.PROP_RSSI_DB: device_event.rssi_db,
        })

        # Notify via callback if needed
        if self._on_event and device_event.event_code is not None:
            try:
                self._on_event(self, device_event.event_code)
            except Exception:
                _LOGGER.error(
                    "Unhandled exception in on_event callback",
                    exc_info=True)

    def _handle_response(self, response: Union[DeviceInfoResponse,
                                               DeviceSettingsResponse]):
        # Update properties
        if isinstance(response, DeviceInfoResponse):
            self._set_field_values({
                Device.PROP_ALARM_HIGH_LIMIT: response.alarm_high_limit,
                Device.PROP_ALARM_LOW_LIMIT: response.alarm_low_limit,
                Device.PROP_CURRENT_READING: response.current_reading,
                Device.PROP_CONTROL_HIGH_LIMIT: response.control_high_limit,
                Device.PROP_CONTROL_LOW_LIMIT: response.control_low_limit,
                Device.PROP_IS_CLOSED: response.is_closed,
                Device.PROP_ENABLE_STATUS: response.enable_status,
                Device.PROP_GROUP_NUMBER: response.group_number,
                Device.PROP_RSSI_BARS: response.rssi_bars,
                Device.PROP_RSSI_DB: response.rssi_db,
                Device.PROP_SPECIAL_STATUS: response.special_status,
                Device.PROP_SWITCHES: response.switches,
                Device.PROP_UNIT_NUMBER: response.unit_number,
                Device.PROP_ZONE: response.zone,
            })
        elif isinstance(response, DeviceSettingsResponse):
            self._set_field_values({
                Device.PROP_ENABLE_STATUS: response.enable_status,
                Device.PROP_GROUP_NUMBER: response.group_number,
                Device.PROP_SWITCHES: response.switches,
                Device.PROP_UNIT_NUMBER: response.unit_number,
                Device.PROP_ZONE: response.zone,
            })

    def _get_field_value(self, property_name: str) -> Any:
        # Get backing field value for specified property name
        return self.__dict__.get('_' + property_name)

    def _set_field_values(self, name_values: Dict[str, Any], notify:bool = True) -> None:
        # Create dictionary to hold changed properties with old / new value
        changes: List[PropertyChangedInfo] = []

        # Process each property to set from caller
        for property_name, new_value in name_values.items():
            # Get the original property value from backing field
            old_value = self.__dict__.get('_' + property_name)

            # Skip if unchanged
            if old_value is None and new_value is None:
                continue
            elif old_value is not None and new_value is not None and old_value == new_value:
                continue

            # Set property to the new value
            info = PropertyChangedInfo(property_name, old_value, new_value)
            self.__dict__['_' + property_name] = info.new_value
            if self._notify_properties_changed:
                _LOGGER.debug(info)

            # Add to collection for later callback
            changes.append(info)

        # Notify via callback if needed
        if len(changes)> 0 and \
                self._notify_properties_changed and \
                self._on_properties_changed:
            try:
                self._on_properties_changed(self, changes)
            except Exception:
                _LOGGER.error(
                    "Unhandled exception in on_properties_changed callback",
                    exc_info=True)


class DeviceCollection(Sized, Iterable, Container):
    """Collection of devices."""

    def __init__(self):
        self._devices: Dict[int, Device] = {}

    #
    # METHODS - Public
    #

    def __contains__(self, device: Union[int, Device]) -> bool:
        """Indicates if specified ID or Device exists in collection."""
        if isinstance(device, int):
            return self._devices.keys().__contains__(device)
        elif isinstance(device, Device):
            return self._devices.keys().__contains__(device.id)
        else:
            return False

    def __getitem__(self, id: int) -> Device:
        """Get device using the specified ID."""
        return self._devices[id]

    def __iter__(self) -> Iterator[Device]:
        """Iterator for the devices in collection."""
        return self._devices.values().__iter__()

    def __len__(self) -> int:
        """Returns number of devices in the collection."""
        return self._devices.__len__()

    def __repr__(self) -> str:
        """Provides an info string for the device collection."""
        len = self.__len__()
        if len == 0:
            return "<DeviceCollection: 0 Devices>"
        else:
            category_count: Dict[DeviceCategory, int] = {}
            for device in self._devices.values():
                category_count[device.category] = \
                    category_count.get(device.category, 0) + 1
            return "<DeviceCollection: {} Devices ({})>".format(
                self.__len__(),
                ", ".join([str(cc[1]) + " " + cc[0].description
                           for cc in category_count.items()]))

    def get(self, id: int) -> Optional[Device]:
        """Get device using the specified ID, or None if not found."""
        return self._devices.get(id)

    #
    # METHODS - Private / Internal
    #

    def _add(self, device: Device) -> None:
        # Add new device to the collection
        self._devices[device.id] = device

    def _delete(self, device: Device) -> None:
        # Delete specified device from collection
        self._devices.pop(device.id)
