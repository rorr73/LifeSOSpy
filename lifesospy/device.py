"""
This module contains the Device class.
"""

import logging
from collections.abc import Sized, Iterable, Container
from typing import (
    Callable, Dict, List, Any, Optional, Union, Iterator)
from lifesospy.devicecategory import DeviceCategory
from lifesospy.deviceevent import DeviceEvent
from lifesospy.enums import (
    DeviceType, DCFlags, ESFlags, SSFlags, DeviceEventCode, SwitchFlags)
from lifesospy.propertychangedinfo import PropertyChangedInfo
from lifesospy.response import DeviceInfoResponse, DeviceSettingsResponse
from lifesospy.util import decode_value_using_ma

_LOGGER = logging.getLogger(__name__)


class Device(object):
    """
    Represents a device that has been enrolled on the base unit.
    """

    # Property names
    PROP_CATEGORY = 'category'
    PROP_CHARACTERISTICS = 'characteristics'
    PROP_DEVICE_ID = 'device_id'
    PROP_ENABLE_STATUS = 'enable_status'
    PROP_GROUP_NUMBER = 'group_number'
    PROP_IS_CLOSED = 'is_closed'
    PROP_MESSAGE_ATTRIBUTE = 'message_attribute'
    PROP_RSSI_BARS = 'rssi_bars'
    PROP_RSSI_DB = 'rssi_db'
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
            Device.PROP_DEVICE_ID: response.device_id,
            Device.PROP_CATEGORY: response.device_category,
            Device.PROP_MESSAGE_ATTRIBUTE: response.message_attribute,
            Device.PROP_TYPE_VALUE: response.device_type_value,
            Device.PROP_TYPE: response.device_type,
            Device.PROP_CHARACTERISTICS: response.device_characteristics,
        })
        self._handle_response(response)
        self._notify_properties_changed = True

    #
    # PROPERTIES
    #

    @property
    def category(self) -> DeviceCategory:
        """Category for the device."""
        return self._get_field_value(Device.PROP_CATEGORY)

    @property
    def characteristics(self) -> DCFlags:
        """Flags indicating the device characteristics."""
        return self._get_field_value(Device.PROP_CHARACTERISTICS)

    @property
    def device_id(self) -> int:
        """Unique identifier for the device."""
        return self._get_field_value(Device.PROP_DEVICE_ID)

    @property
    def enable_status(self) -> ESFlags:
        """Flags indicating settings that have been enabled."""
        return self._get_field_value(Device.PROP_ENABLE_STATUS)

    @property
    def group_number(self) -> int:
        """Group number the device is assigned to."""
        return self._get_field_value(Device.PROP_GROUP_NUMBER)

    @property
    def is_closed(self) -> Optional[bool]:
        """For Magnet Sensor; True if Closed, False if Open."""
        return self._get_field_value(Device.PROP_IS_CLOSED)

    @property
    def message_attribute(self) -> int:
        """Message attribute; used to encode/decode Special device values."""
        return self._get_field_value(Device.PROP_MESSAGE_ATTRIBUTE)

    @property
    def rssi_bars(self) -> int:
        """Received Signal Strength Indication, from 0 to 4 bars."""
        return self._get_field_value(Device.PROP_RSSI_BARS)

    @property
    def rssi_db(self) -> int:
        """Received Signal Strength Indication, in dB."""
        return self._get_field_value(Device.PROP_RSSI_DB)

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
        return "<{}: device_id={:06x}, type_value={:02x}, type={}, " \
               "category.description={}, zone={}, rssi_db={}{}, characteristics={}, " \
               "enable_status={}, switches={}>".format(
                   self.__class__.__name__,
                   self.device_id,
                   self.type_value,
                   str(self.type),
                   self.category.description,
                   self.zone,
                   self.rssi_db,
                   '' if self.type_value != DeviceType.DoorMagnet else
                   ", is_closed={}".format(self.is_closed),
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
        changes: Dict[str, Any] = {
            Device.PROP_IS_CLOSED: is_closed,
            Device.PROP_RSSI_BARS: device_event.rssi_bars,
            Device.PROP_RSSI_DB: device_event.rssi_db,
        }
        changes.update(self._get_device_event_changes(device_event))
        self._set_field_values(changes)

        # Notify via callback if needed
        if self._on_event and device_event.event_code is not None:
            try:
                self._on_event(self, device_event.event_code)
            except Exception: # pylint: disable=broad-except
                _LOGGER.error(
                    "Unhandled exception in on_event callback",
                    exc_info=True)

    def _get_device_event_changes(self, device_event: DeviceEvent) -> Dict[str, Any]: # pylint: disable=no-self-use
        # Override this to provide any additional property changes
        return {}

    def _handle_response(self, response: Union[DeviceInfoResponse,
                                               DeviceSettingsResponse]):
        # Update properties
        if isinstance(response, DeviceInfoResponse):
            changes = {
                Device.PROP_ENABLE_STATUS: response.enable_status,
                Device.PROP_GROUP_NUMBER: response.group_number,
                Device.PROP_IS_CLOSED: response.is_closed,
                Device.PROP_RSSI_BARS: response.rssi_bars,
                Device.PROP_RSSI_DB: response.rssi_db,
                Device.PROP_SWITCHES: response.switches,
                Device.PROP_UNIT_NUMBER: response.unit_number,
                Device.PROP_ZONE: response.zone,
            }
        elif isinstance(response, DeviceSettingsResponse):
            changes = {
                Device.PROP_ENABLE_STATUS: response.enable_status,
                Device.PROP_GROUP_NUMBER: response.group_number,
                Device.PROP_SWITCHES: response.switches,
                Device.PROP_UNIT_NUMBER: response.unit_number,
                Device.PROP_ZONE: response.zone,
            }
        else:
            return
        changes.update(self._get_response_changes(response))
        self._set_field_values(changes)

    def _get_response_changes( # pylint: disable=no-self-use
            self, response: Union[DeviceInfoResponse, DeviceSettingsResponse]) \
            -> Dict[str, Any]:
        # Override this to provide any additional property changes
        return {}

    def _get_field_value(self, property_name: str) -> Any:
        # Get backing field value for specified property name
        return self.__dict__.get('_' + property_name)

    def _set_field_values(self, name_values: Dict[str, Any], notify: bool = True) -> None:
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
        if changes and \
                self._notify_properties_changed and \
                self._on_properties_changed:
            try:
                self._on_properties_changed(self, changes)
            except Exception: # pylint: disable=broad-except
                _LOGGER.error(
                    "Unhandled exception in on_properties_changed callback",
                    exc_info=True)


class SpecialDevice(Device):
    """
    Represents a Special device that has been enrolled on the base unit.
    """

    # Property names
    PROP_CONTROL_HIGH_LIMIT = 'control_high_limit'
    PROP_CONTROL_LIMIT_FIELDS_EXIST = 'control_limit_fields_exist'
    PROP_CONTROL_LOW_LIMIT = 'control_low_limit'
    PROP_CURRENT_READING = 'current_reading'
    PROP_HIGH_LIMIT = 'high_limit'
    PROP_LOW_LIMIT = 'low_limit'
    PROP_SPECIAL_STATUS = 'special_status'

    def __init__(self, response: DeviceInfoResponse):
        Device.__init__(self, response)

        # Init fixed and variable property values
        self._notify_properties_changed = False
        self._set_field_values({
            SpecialDevice.PROP_CONTROL_LIMIT_FIELDS_EXIST: response.control_limit_fields_exist,
        })
        self._handle_response(response)
        self._notify_properties_changed = True

    #
    # PROPERTIES
    #

    @property
    def control_high_limit(self) -> Optional[Union[int, float]]:
        """
        Control high limit setting for a special sensor.

        For LS-10/LS-20 base units only.
        """
        return self._get_field_value(SpecialDevice.PROP_CONTROL_HIGH_LIMIT)

    @property
    def control_limit_fields_exist(self) -> bool:
        """
        True if control limit fields exist; otherwise, False.

        Only the LS-10/LS-20 base units provide these separate control limits,
        with high_limit/low_limit exclusively holding the alarm limits.
        On the LS-30, high_limit/low_limit can be either alarm OR control
        limits (mode indicated by the special_status ControlAlarm bit flag).
        """
        return self._get_field_value(SpecialDevice.PROP_CONTROL_LIMIT_FIELDS_EXIST)

    @property
    def control_low_limit(self) -> Optional[Union[int, float]]:
        """
        Control low limit setting for a special sensor.

        For LS-10/LS-20 base units only.
        """
        return self._get_field_value(SpecialDevice.PROP_CONTROL_LOW_LIMIT)

    @property
    def current_reading(self) -> Optional[Union[int, float]]:
        """Current reading for a special sensor."""
        return self._get_field_value(SpecialDevice.PROP_CURRENT_READING)

    @property
    def high_limit(self) -> Optional[Union[int, float]]:
        """
        High limit setting for a special sensor.

        For LS-10/LS-20 base units this is the alarm high limit.
        For LS-30 base units, this is either alarm OR control high limit,
        as indicated by special_status ControlAlarm bit flag.
        """
        return self._get_field_value(SpecialDevice.PROP_HIGH_LIMIT)

    @property
    def low_limit(self) -> Optional[Union[int, float]]:
        """
        Low limit setting for a special sensor.

        For LS-10/LS-20 base units this is the alarm low limit.
        For LS-30 base units, this is either alarm OR control low limit,
        as indicated by special_status ControlAlarm bit flag.
        """
        return self._get_field_value(SpecialDevice.PROP_LOW_LIMIT)

    @property
    def special_status(self) -> SSFlags:
        """Special sensor status flags."""
        return self._get_field_value(SpecialDevice.PROP_SPECIAL_STATUS)

    #
    # METHODS - Public
    #

    def __repr__(self) -> str:
        """Provides an info string for the device."""
        special = ", current_reading={}, special_status={}, high_limit={}, low_limit={}".format(
            self.current_reading,
            str(self.special_status),
            self.high_limit,
            self.low_limit)
        if self.control_limit_fields_exist:
            special += ", control_high_limit={}, control_low_limit={}".format(
                self.control_high_limit,
                self.control_low_limit)
        text = Device.__repr__(self)
        text = text[:len(text)-1] + special + text[len(text)-1:]
        return text

    #
    # METHODS - Private / Internal
    #

    def _get_device_event_changes(self, device_event: DeviceEvent) -> Dict[str, Any]:
        return {
            SpecialDevice.PROP_CURRENT_READING: device_event.current_reading,
        }

    def _get_response_changes(
            self, response: Union[DeviceInfoResponse, DeviceSettingsResponse]) \
            -> Dict[str, Any]:
        changes = {}
        if isinstance(response, DeviceInfoResponse):
            changes.update({
                SpecialDevice.PROP_CURRENT_READING: response.current_reading,
                SpecialDevice.PROP_HIGH_LIMIT: response.high_limit,
                SpecialDevice.PROP_LOW_LIMIT: response.low_limit,
                SpecialDevice.PROP_SPECIAL_STATUS: response.special_status,
            })
            if self.control_limit_fields_exist:
                changes.update({
                    SpecialDevice.PROP_CONTROL_HIGH_LIMIT: response.control_high_limit,
                    SpecialDevice.PROP_CONTROL_LOW_LIMIT: response.control_low_limit,
                })
        elif isinstance(response, DeviceSettingsResponse) and response.special_fields_exist:
            changes.update({
                SpecialDevice.PROP_CURRENT_READING: decode_value_using_ma(
                    self.message_attribute, response.current_reading_encoded),
                SpecialDevice.PROP_HIGH_LIMIT: decode_value_using_ma(
                    self.message_attribute, response.high_limit_encoded),
                SpecialDevice.PROP_LOW_LIMIT: decode_value_using_ma(
                    self.message_attribute, response.low_limit_encoded),
                SpecialDevice.PROP_SPECIAL_STATUS: response.special_status,
            })
            if self.control_limit_fields_exist:
                changes.update({
                    SpecialDevice.PROP_CONTROL_HIGH_LIMIT: decode_value_using_ma(
                        self.message_attribute, response.control_high_limit_encoded),
                    SpecialDevice.PROP_CONTROL_LOW_LIMIT: decode_value_using_ma(
                        self.message_attribute, response.control_low_limit_encoded),
                })
        return changes


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
            return self._devices.keys().__contains__(device.device_id)
        return False

    def __getitem__(self, device_id: int) -> Device:
        """Get device using the specified ID."""
        return self._devices[device_id]

    def __iter__(self) -> Iterator[Device]:
        """Iterator for the devices in collection."""
        return self._devices.values().__iter__()

    def __len__(self) -> int:
        """Returns number of devices in the collection."""
        return self._devices.__len__()

    def __repr__(self) -> str:
        """Provides an info string for the device collection."""
        category_count: Dict[DeviceCategory, int] = {}
        for device in self._devices.values():
            category_count[device.category] = \
                category_count.get(device.category, 0) + 1
        return "<{}: {} Total ({})>".format(
            self.__class__.__name__,
            self.__len__(),
            ", ".join([str(cc[1]) + " " + cc[0].description
                       for cc in category_count.items()]))

    def get(self, device_id: int) -> Optional[Device]:
        """Get device using the specified ID, or None if not found."""
        return self._devices.get(device_id)

    #
    # METHODS - Private / Internal
    #

    def _add(self, device: Device) -> None:
        # Add new device to the collection
        self._devices[device.device_id] = device

    def _delete(self, device: Device) -> None:
        # Delete specified device from collection
        self._devices.pop(device.device_id)
