"""
This module contains the BaseUnit class.
"""

import logging
from collections import OrderedDict
from datetime import datetime
from typing import Callable, Any, Dict, List, Optional, Union
from lifesospy.asynchelper import AsyncHelper
from lifesospy.client import Client
from lifesospy.command import (
    Command, GetDeviceCommand, GetDeviceByIndexCommand, GetROMVersionCommand,
    GetExitDelayCommand, GetEntryDelayCommand, SetDateTimeCommand,
    ClearStatusCommand, AddDeviceCommand, ChangeDeviceCommand,
    ChangeSpecialDeviceCommand, ChangeSpecial2DeviceCommand,
    DeleteDeviceCommand, GetEventLogCommand, GetSensorLogCommand,
    GetOpModeCommand, SetOpModeCommand, GetSwitchCommand, SetSwitchCommand)
from lifesospy.contactid import ContactID
from lifesospy.device import Device, SpecialDevice, DeviceCollection
from lifesospy.devicecategory import (
    DeviceCategory, DC_CONTROLLER, DC_BURGLAR, DC_SPECIAL, DC_ALL)
from lifesospy.deviceevent import DeviceEvent
from lifesospy.enums import (
    OperationMode, BaseUnitState, ESFlags, SSFlags, SwitchFlags, SwitchNumber,
    SwitchState, ContactIDEventCategory, ContactIDEventQualifier,
    ContactIDEventCode, DeviceEventCode)
from lifesospy.propertychangedinfo import PropertyChangedInfo
from lifesospy.response import (
    Response, OpModeResponse, ROMVersionResponse, ExitDelayResponse,
    EntryDelayResponse, DateTimeResponse, DeviceInfoResponse,
    DeviceSettingsResponse, DeviceNotFoundResponse, DeviceAddedResponse,
    DeviceDeletedResponse, EventLogResponse, SensorLogResponse, SwitchResponse)

_LOGGER = logging.getLogger(__name__)


class BaseUnit(AsyncHelper):
    """
    Represents the base unit.

    Provides all management of the LifeSOS alarm system, monitoring attached
    devices, events, and is used to issue commands. It will also attempt
    reconnection automatically on failure.

    Your application can either use this class to provide management / higher
    level access, or the Client class for direct access.
    """

    # Property names
    PROP_ENTRY_DELAY = 'entry_delay'
    PROP_EXIT_DELAY = 'exit_delay'
    PROP_IS_CONNECTED = 'is_connected'
    PROP_OPERATION_MODE = 'operation_mode'
    PROP_ROM_VERSION = 'rom_version'
    PROP_STATE = 'state'

    # Default interval to wait between reconnect attempts
    RECONNECT_INTERVAL = 30

    # Allow this many retries when getting initial state
    RETRY_MAX = 3

    def __init__(self, host: str, port: int):
        AsyncHelper.__init__(self)
        self._client = Client(host, port)
        self._shutdown = False
        self._reconnect_interval = BaseUnit.RECONNECT_INTERVAL
        self._on_device_added = None
        self._on_device_deleted = None
        self._on_event = None
        self._on_properties_changed = None
        self._on_switch_state_changed = None

        # Init default property values where needed
        self._notify_properties_changed = False
        self._set_field_values({
            BaseUnit.PROP_IS_CONNECTED: False,
        })
        self._notify_properties_changed = True

        # Create collection to hold all enrolled devices
        self._devices = DeviceCollection()

        # Create dictionary to hold state for each switch
        self._switch_state = OrderedDict()
        for switch_number in SwitchNumber:
            self._switch_state[switch_number] = None

        # Assign callbacks to capture all client events
        self._client.on_connection_made = self._handle_connection_made
        self._client.on_connection_lost = self._handle_connection_lost
        self._client.on_contact_id = self._handle_contact_id
        self._client.on_device_event = self._handle_device_event
        self._client.on_response = self._handle_response

    #
    # PROPERTIES
    #

    @property
    def devices(self) -> DeviceCollection:
        """Devices enrolled on the base unit."""
        return self._devices

    @property
    def entry_delay(self) -> int:
        """Entry delay, in seconds."""
        return self._get_field_value(BaseUnit.PROP_ENTRY_DELAY)

    @property
    def exit_delay(self) -> int:
        """Exit delay, in seconds."""
        return self._get_field_value(BaseUnit.PROP_EXIT_DELAY)

    @property
    def host(self) -> str:
        """Host name or IP address for the LifeSOS ethernet interface."""
        return self._client.host

    @property
    def is_connected(self) -> bool:
        """True if connected to the base unit; otherwise, False."""
        return self._get_field_value(BaseUnit.PROP_IS_CONNECTED)

    @property
    def operation_mode(self) -> OperationMode:
        """Operation mode."""
        return self._get_field_value(BaseUnit.PROP_OPERATION_MODE)

    @property
    def password(self) -> str:
        """Control password, if one has been assigned on the base unit."""
        return self._client.password

    @password.setter
    def password(self, password: str):
        self._client.password = password

    @property
    def port(self) -> int:
        """Port number for the LifeSOS ethernet interface."""
        return self._client.port

    @property
    def reconnect_interval(self) -> int:
        """Interval to wait between reconnect attempts."""
        return self._reconnect_interval

    @property
    def rom_version(self) -> str:
        """ROM version string."""
        return self._get_field_value(BaseUnit.PROP_ROM_VERSION)

    @property
    def state(self) -> BaseUnitState:
        """Current state of the base unit."""
        return self._get_field_value(BaseUnit.PROP_STATE)

    @property
    def switch_state(self) -> Dict[SwitchNumber, Optional[bool]]:
        """Current state for each switch on the base unit."""
        return self._switch_state.copy()

    #
    # EVENTS
    #

    @property
    def on_device_added(self) -> Callable[['BaseUnit', Device], None]:
        """If implemented, called after a device has been discovered or added."""
        return self._on_device_added

    @on_device_added.setter
    def on_device_added(self, func: Callable[['BaseUnit', Device], None]):
        """
        Define the device added callback implementation.

        Expected signature is:
            device_added_callback(base_unit, device)

        base_unit:      the base unit instance for this callback
        device:         the device instance that was added
        """
        self._on_device_added = func

    @property
    def on_device_deleted(self) -> Callable[['BaseUnit', Device], None]:
        """If implemented, called after a device has been deleted."""
        return self._on_device_deleted

    @on_device_deleted.setter
    def on_device_deleted(self, func: Callable[['BaseUnit', Device], None]):
        """
        Define the device deleted callback implementation.

        Expected signature is:
            device_deleted_callback(base_unit, device)

        base_unit:      the base unit instance for this callback
        device:         the device instance that was deleted
        """
        self._on_device_deleted = func

    @property
    def on_event(self) -> Callable[['BaseUnit', ContactID], None]:
        """If implemented, called when an event occurs."""
        return self._on_event

    @on_event.setter
    def on_event(self, func: Callable[['BaseUnit', ContactID], None]) -> None:
        """
        Define the event callback implementation.

        Expected signature is:
            event_callback(base_unit, contact_id)

        base_unit:      the base unit instance for this callback
        contact_id:     provides details for the event.
        """
        self._on_event = func

    @property
    def on_properties_changed(self) -> Callable[['BaseUnit', List[PropertyChangedInfo]], None]:
        """If implemented, called after property values have been changed."""
        return self._on_properties_changed

    @on_properties_changed.setter
    def on_properties_changed(self, func: Callable[['BaseUnit', List[PropertyChangedInfo]], None]):
        """
        Define the properties changed callback implementation.

        Expected signature is:
            properties_changed_callback(base_unit, dict)

        base_unit:      the device instance for this callback
        changes:        list providing name and values of changed properties
        """
        self._on_properties_changed = func

    @property
    def on_switch_state_changed(self) \
            -> Callable[['BaseUnit', SwitchNumber, Optional[bool]], None]:
        """If implemented, called when the state of a switch has changed."""
        return self._on_switch_state_changed

    @on_switch_state_changed.setter
    def on_switch_state_changed(
            self, func: Callable[['BaseUnit', SwitchNumber, Optional[bool]], None]):
        """
        Define the switch state changed callback implementation.

        Expected signature is:
            switch_state_changed_callback(base_unit, switch_number, state)

        base_unit:      the device instance for this callback
        switch_number:  the switch whose state has changed
        state:          True if switch turned on, or False if switch turned off
        """
        self._on_switch_state_changed = func

    #
    # METHODS - Public
    #

    def start(self) -> None:
        """
        Start monitoring the base unit.
        """

        self._shutdown = False

        # Attempt to open client connection and schedule retry if needed
        self.create_task(self._async_open)

    def stop(self) -> None:
        """
        Stop monitoring the base unit.
        """

        self._shutdown = True

        # Close client connection if needed
        self._client.close()

        # Cancel any pending tasks
        self.cancel_pending_tasks()

    async def async_clear_status(self, password: str = '') -> None:
        """
        Clear the alarm/warning LEDs on base unit and stop siren.

        :param password: if specified, will be used instead of the password
                         property when issuing the command
        """

        await self._client.async_execute(
            ClearStatusCommand(),
            password=password)

    async def async_add_device(self, category: DeviceCategory) -> None:
        """
        Enroll a new device on the base unit.

        :param category: category of device the base unit will listen for.
        """

        await self._client.async_execute(
            AddDeviceCommand(category))

    async def async_change_device(
            self, device_id: int, group_number: int, unit_number: int,
            enable_status: ESFlags, switches: SwitchFlags) -> None:
        """
        Change settings for a device on the base unit.

        :param device_id: unique identifier for the device to be changed
        :param group_number: group number the device is to be assigned to
        :param unit_number: unit number the device is to be assigned to
        :param enable_status: flags indicating settings to enable
        :param switches: indicates switches that will be activated when device is triggered
        """

        # Lookup device using zone to obtain an accurate index and current
        # values, which will be needed to perform the change command
        device = self._devices[device_id]

        # If it is a Special device, automatically use the other function
        # instead (without changing any of the special fields)
        if isinstance(device, SpecialDevice):
            await self.async_change_special_device(
                device_id, group_number, unit_number, enable_status, switches,
                device.special_status, device.high_limit, device.low_limit,
                device.control_high_limit, device.control_low_limit)
            return

        response = await self._client.async_execute(
            GetDeviceCommand(device.category, device.group_number, device.unit_number))
        if isinstance(response, DeviceInfoResponse):
            response = await self._client.async_execute(
                ChangeDeviceCommand(
                    device.category, response.index, group_number, unit_number,
                    enable_status, switches))
            if isinstance(response, DeviceSettingsResponse):
                device._handle_response(response) # pylint: disable=protected-access
        if isinstance(response, DeviceNotFoundResponse):
            raise ValueError("Device to be changed was not found")

    async def async_change_special_device(
            self, device_id: int, group_number: int, unit_number: int,
            enable_status: ESFlags, switches: SwitchFlags,
            special_status: SSFlags, high_limit: Optional[Union[int, float]],
            low_limit: Optional[Union[int, float]],
            control_high_limit: Optional[Union[int, float]],
            control_low_limit: Optional[Union[int, float]]) -> None:
        """
        Change settings for a 'Special' device on the base unit.

        :param device_id: unique identifier for the device to be changed
        :param group_number: group number the device is to be assigned to
        :param unit_number: unit number the device is to be assigned to
        :param enable_status: flags indicating settings to enable
        :param switches: indicates switches that will be activated when device is triggered
        :param special_status: flags indicating 'Special' settings to enable
        :param high_limit: triggers on readings higher than value
        :param low_limit: triggers on readings lower than value
        :param control_high_limit: trigger switch for readings higher than value
        :param control_low_limit: trigger switch for readings lower than value
        """

        # Lookup device using zone to obtain an accurate index and current
        # values, which will be needed to perform the change command
        device = self._devices[device_id]

        # Verify it is a Special device
        if not isinstance(device, SpecialDevice):
            raise ValueError("Device to be changed is not a Special device")

        response = await self._client.async_execute(
            GetDeviceCommand(device.category, device.group_number, device.unit_number))
        if isinstance(response, DeviceInfoResponse):
            # Control limits only specified when they are supported
            if response.control_limit_fields_exist:
                command = ChangeSpecial2DeviceCommand(
                    device.category, response.index, group_number, unit_number,
                    enable_status, switches, response.current_status, response.down_count,
                    response.message_attribute, response.current_reading, special_status,
                    high_limit, low_limit, control_high_limit, control_low_limit)
            else:
                command = ChangeSpecialDeviceCommand(
                    device.category, response.index, group_number, unit_number,
                    enable_status, switches, response.current_status, response.down_count,
                    response.message_attribute, response.current_reading, special_status,
                    high_limit, low_limit)
            response = await self._client.async_execute(command)
            if isinstance(response, DeviceSettingsResponse):
                device._handle_response(response) # pylint: disable=protected-access
        if isinstance(response, DeviceNotFoundResponse):
            raise ValueError("Device to be changed was not found")

    async def async_delete_device(self, device_id: int) -> None:
        """
        Delete an enrolled device.

        :param device_id: unique identifier for the device to be deleted
        """

        # Lookup device using zone to obtain an accurate index, which is
        # needed to perform the delete command
        device = self._devices[device_id]
        response = await self._client.async_execute(
            GetDeviceCommand(device.category, device.group_number, device.unit_number))
        if isinstance(response, DeviceInfoResponse):
            response = await self._client.async_execute(
                DeleteDeviceCommand(device.category, response.index))
            if isinstance(response, DeviceDeletedResponse):
                self._devices._delete(device) # pylint: disable=protected-access
                if self._on_device_deleted:
                    try:
                        self._on_device_deleted(self, device)  # pylint: disable=protected-access
                    except Exception: # pylint: disable=broad-except
                        _LOGGER.error(
                            "Unhandled exception in on_device_deleted callback",
                            exc_info=True)
        if isinstance(response, DeviceNotFoundResponse):
            raise ValueError("Device to be deleted was not found")

    async def async_get_event_log(self, index: int) -> Optional[EventLogResponse]:
        """
        Get an entry from the event log.

        :param index: Index for the event log entry to be obtained.
        :return: Response containing the event log entry, or None if not found.
        """

        response = await self._client.async_execute(
            GetEventLogCommand(index))
        if isinstance(response, EventLogResponse):
            return response
        return None

    async def async_get_sensor_log(self, index: int) -> Optional[SensorLogResponse]:
        """
        Get an entry from the Special sensor log.

        :param index: Index for the sensor log entry to be obtained.
        :return: Response containing the sensor log entry, or None if not found.
        """

        response = await self._client.async_execute(
            GetSensorLogCommand(index))
        if isinstance(response, SensorLogResponse):
            return response
        return None

    async def async_set_datetime(self, value: datetime = None) -> None:
        """
        Set the date/time on the base unit.

        :param datetime: if specified, the date/time to be set on the base unit.
                         if not specified or none, the current date/time is used.
        """

        await self._client.async_execute(
            SetDateTimeCommand(value))

    async def async_set_operation_mode(
            self, operation_mode: OperationMode, password: str = '') -> None:
        """
        Set the operation mode on the base unit.

        :param operation_mode: the operation mode to change to
        :param password: if specified, will be used instead of the password
                         property when issuing the command
        """

        await self._client.async_execute(
            SetOpModeCommand(operation_mode),
            password=password)

    async def async_set_switch_state(
            self, switch_number: SwitchNumber, state: bool) -> None:
        """
        Turn a switch on or off.

        :param switch_number: the switch to be set.
        :param state: True to turn on, False to turn off.
        """

        await self._client.async_execute(
            SetSwitchCommand(
                switch_number,
                SwitchState.On if state else SwitchState.Off))

    def __repr__(self) -> str:
        """Provides an info string for the base unit."""
        return "<{}: is_connected={}, state={}>".\
            format(self.__class__.__name__,
                   self.is_connected,
                   str(self.state))

    #
    # METHODS - Private / Internal
    #

    async def _async_open(self) -> None:
        _LOGGER.debug("Connecting")
        try:
            await self._client.async_open()
        except Exception: # pylint: disable=broad-except
            _LOGGER.error("Failed to open client connection. Will retry in %s seconds",
                          self._reconnect_interval, exc_info=True)
            self._loop.call_later(self._reconnect_interval, self._reconnect)

    def _reconnect(self) -> None:
        if self._shutdown:
            return
        self.create_task(self._async_open)

    def _handle_connection_made(self, client: Client) -> None:
        _LOGGER.info("Connected successfully")
        self._set_field_values({BaseUnit.PROP_IS_CONNECTED: True})

        # Get initial state info and find devices
        self.create_task(self._async_get_initial_state)

    async def _async_get_initial_state(self) -> None:
        _LOGGER.info("Discovering devices and getting initial state...")

        # ROM version may be useful for determining features and commands
        # supported by base unit. May also help with diagnosing issues
        await self._async_execute_retry(
            GetROMVersionCommand(), "Failed to get ROM version")

        # Get the initial operation mode, exit and entry delay
        await self._async_execute_retry(
            GetOpModeCommand(), "Failed to get initial operation mode")
        await self._async_execute_retry(
            GetExitDelayCommand(), "Failed to get exit delay")
        await self._async_execute_retry(
            GetEntryDelayCommand(), "Failed to get entry delay")

        # Iterate through all enrolled devices
        for category in DC_ALL:
            if category.max_devices:
                for index in range(0, category.max_devices):
                    response = await self._async_execute_retry(
                        GetDeviceByIndexCommand(category, index),
                        "Failed to get {} device #{}".format(
                            category.description, index))
                    if response is None or \
                            isinstance(response, DeviceNotFoundResponse):
                        break

        # Get initial state information for each switch
        for switch_number in SwitchNumber:
            await self._async_execute_retry(
                GetSwitchCommand(switch_number),
                "Failed to get initial switch {} state".format(str(switch_number)))

        _LOGGER.info("Device discovery completed and got initial state")

    def _handle_connection_lost(self, client: Client, ex: Exception) -> None:
        _LOGGER.error("Connection was lost. Will attempt to reconnect in %s seconds",
                      self._reconnect_interval, exc_info=ex)
        self._set_field_values({BaseUnit.PROP_IS_CONNECTED: False})
        self._loop.call_later(self._reconnect_interval, self._reconnect)

    def _handle_contact_id(self, client: Client, contact_id: ContactID) -> None:
        # Skip if event code was unrecognised
        if contact_id.event_code is None:
            return

        # Change of operation mode
        if contact_id.event_code == ContactIDEventCode.Away or \
                contact_id.event_code == ContactIDEventCode.Away_QuickArm:
            self._set_field_values({
                BaseUnit.PROP_OPERATION_MODE: OperationMode.Away,
                BaseUnit.PROP_STATE: BaseUnitState.Away})
        elif contact_id.event_code == ContactIDEventCode.Home:
            self._set_field_values({
                BaseUnit.PROP_OPERATION_MODE: OperationMode.Home,
                BaseUnit.PROP_STATE: BaseUnitState.Home})
        elif contact_id.event_code == ContactIDEventCode.Disarm:
            self._set_field_values({
                BaseUnit.PROP_OPERATION_MODE: OperationMode.Disarm,
                BaseUnit.PROP_STATE: BaseUnitState.Disarm})
        elif contact_id.event_code == ContactIDEventCode.MonitorMode:
            self._set_field_values({
                BaseUnit.PROP_OPERATION_MODE: OperationMode.Monitor,
                BaseUnit.PROP_STATE: BaseUnitState.Monitor})

        # Alarm has been triggered
        elif contact_id.event_category == ContactIDEventCategory.Alarm and \
                contact_id.event_qualifier == ContactIDEventQualifier.Event:
            # When entry delay expired, return state to Away mode
            if self.state == BaseUnitState.AwayEntryDelay:
                self._set_field_values({
                    BaseUnit.PROP_STATE: BaseUnitState.Away})

        # Notify via callback if needed
        if self._on_event:
            try:
                self._on_event(self, contact_id)
            except Exception: # pylint: disable=broad-except
                _LOGGER.error(
                    "Unhandled exception in on_event callback",
                    exc_info=True)

    def _handle_device_event(self, client: Client, device_event: DeviceEvent) -> None:
        # Get device; there is a chance it may not exist when:
        #  - Client has just connected but has not yet enumerated devices, in
        #    which case we can just ignore since we'll be getting the info later
        #  - Device was enrolled after we enumerated devices. The base unit doesn't
        #    provide any event when this happens (on my firmware at least), so we
        #    can't do much about it
        device = self._devices.get(device_event.device_id)
        if device is None:
            _LOGGER.debug("Event for device not in our collection: Id %06x",
                          device_event.device_id)
            return

        # Provide device with event
        device._handle_device_event(device_event) # pylint: disable=protected-access

        # When a remote controller signals operation mode change it normally
        # takes effect immediately, unless switching to Away mode and there is
        # an exit delay set, in which case we'll need to indicate we're
        # delaying the change to Away mode
        if device_event.event_code == DeviceEventCode.Away and \
                (self.operation_mode is None or
                 self.operation_mode != OperationMode.Away):
            # Away mode change is deferred if exit delay set
            if device.category == DC_CONTROLLER and \
                    not (device.enable_status & ESFlags.Bypass) and \
                    device.enable_status & ESFlags.Delay and \
                    self.exit_delay is not None and self.exit_delay > 0:
                self._set_field_values({BaseUnit.PROP_STATE: BaseUnitState.AwayExitDelay})
            else:
                self._set_field_values({
                    BaseUnit.PROP_OPERATION_MODE: OperationMode.Away,
                    BaseUnit.PROP_STATE: BaseUnitState.Away})
        elif device_event.event_code == DeviceEventCode.Home:
            self._set_field_values({
                BaseUnit.PROP_OPERATION_MODE: OperationMode.Home,
                BaseUnit.PROP_STATE: BaseUnitState.Home})
        elif device_event.event_code == DeviceEventCode.Disarm:
            self._set_field_values({
                BaseUnit.PROP_OPERATION_MODE: OperationMode.Disarm,
                BaseUnit.PROP_STATE: BaseUnitState.Disarm})

        # When a burglar sensor is tripped while in Away mode and an entry
        # delay has been set, we'll need to indicate we're delaying the alarm
        if device_event.event_code in [DeviceEventCode.Trigger,
                                       DeviceEventCode.Open] and \
                self.operation_mode == OperationMode.Away:
            if device.category == DC_BURGLAR and \
                    not (device.enable_status & ESFlags.Bypass) and \
                    device.enable_status & ESFlags.Delay and \
                    not (device.enable_status & ESFlags.Inactivity) and \
                    self.entry_delay is not None and self.entry_delay > 0:
                self._set_field_values(
                    {BaseUnit.PROP_STATE: BaseUnitState.AwayEntryDelay})

    def _handle_response(self, client: Client, response: Response, command: Command) -> None:
        # Update any properties of the base unit
        if isinstance(response, ROMVersionResponse):
            self._set_field_values({
                BaseUnit.PROP_ROM_VERSION: response.version})
        elif isinstance(response, OpModeResponse):
            self._set_field_values({
                BaseUnit.PROP_OPERATION_MODE: response.operation_mode,
                BaseUnit.PROP_STATE: BaseUnitState.from_operation_mode(response.operation_mode)})
        elif isinstance(response, ExitDelayResponse):
            self._set_field_values({
                BaseUnit.PROP_EXIT_DELAY: response.exit_delay})
        elif isinstance(response, EntryDelayResponse):
            self._set_field_values({
                BaseUnit.PROP_ENTRY_DELAY: response.entry_delay})

        elif isinstance(response, DateTimeResponse):
            # Log changes to remote date/time
            if response.was_set:
                _LOGGER.info(
                    "Remote date/time %s %s",
                    'is' if not response.was_set else "was set to",
                    response.remote_datetime.strftime('%a %d %b %Y %I:%M %p'))

        elif isinstance(response, DeviceInfoResponse):
            # Add / Update a device
            device = self._devices.get(response.device_id)
            if device is None:
                if response.device_category == DC_SPECIAL:
                    device = SpecialDevice(response)
                else:
                    device = Device(response)
                self._devices._add(device) # pylint: disable=protected-access
                if self._on_device_added:
                    try:
                        self._on_device_added(self, device)
                    except Exception: # pylint: disable=broad-except
                        _LOGGER.error(
                            "Unhandled exception in on_device_added callback",
                            exc_info=True)
            else:
                device._handle_response(response) # pylint: disable=protected-access

        elif isinstance(response, DeviceAddedResponse):
            # New device enrolled; the info is insufficient so we'll need
            # to issue a command to get the full device info
            self.create_task(
                self._async_execute_retry,
                GetDeviceByIndexCommand(response.device_category,
                                        response.index),
                "Failed to get new {} device #{}".format(
                    response.device_category.description,
                    response.index))

        elif isinstance(response, SwitchResponse):
            # Switch state change
            self._set_switch_state(
                response.switch_number,
                None if response.switch_state is None
                else True if response.switch_state == SwitchState.On else False)

    def _set_switch_state(self, switch_number: SwitchNumber, new_state: Optional[bool]) -> None:
        # Get the original switch state
        old_state = self._switch_state[switch_number]

        # Skip if unchanged
        if old_state is None and new_state is None:
            return
        if old_state is not None and new_state is not None and old_state == new_state:
            return

        # Set switch to new state
        self._switch_state[switch_number] = new_state
        _LOGGER.debug("Switch %s changed from %s to %s",
                      str(switch_number),
                      "Unknown" if old_state is None else "On" if old_state else "Off",
                      "Unknown" if new_state is None else "On" if new_state else "Off")

        # Notify via callback if needed
        if self._on_switch_state_changed:
            try:
                self._on_switch_state_changed(self, switch_number, new_state)
            except Exception: # pylint: disable=broad-except
                _LOGGER.error(
                    "Unhandled exception in on_switch_state_changed callback",
                    exc_info=True)

    async def _async_execute_retry(self, command: Command, error_message: str,
                                   max_retries: int = RETRY_MAX) \
            -> Optional[Response]:
        # Execute a command and return response if successful; but retry if an
        # error occurs, up to the specified number of attempts. This can be
        # useful given the LS-30 comes with a dodgy unshielded serial cable.
        for attempt in range(1, max_retries + 1):
            if self._shutdown or not self.is_connected:
                return None
            try:
                return await self._client.async_execute(command)
            except ConnectionError:
                # Client no longer connected; don't bother retrying
                return None
            except Exception: # pylint: disable=broad-except
                _LOGGER.error("%s [Attempt %s/%s]",
                              error_message, attempt, max_retries,
                              exc_info=True)
        return None

    def _get_field_value(self, property_name: str) -> Any:
        # Get backing field value for specified property name
        return self.__dict__.get('_' + property_name)

    def _set_field_values(self, name_values: Dict[str, Any], notify: bool = True) -> None:
        # Create dictionary to hold changed properties with old / new value
        changes = []

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
