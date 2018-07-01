"""
This module contains the Client class.
"""

import asyncio
import logging
import time
from typing import Callable, Dict, Any
from lifesospy.asynchelper import AsyncHelper
from lifesospy.command import Command, NoOpCommand
from lifesospy.const import MARKER_START, MARKER_END, CMD_SENSOR_LOG
from lifesospy.contactid import ContactID
from lifesospy.deviceevent import DeviceEvent
from lifesospy.response import Response

_LOGGER = logging.getLogger(__name__)


class Client(asyncio.Protocol, AsyncHelper):
    """
    Provides connectivity to the LifeSOS ethernet interface.

    Your application can either use this class for direct access to LifeSOS,
    or use the BaseUnit class to provide management / higher level access.
    """

    # Ensure connection still alive when no data sent/recieved after this many seconds
    ENSURE_ALIVE_SECS = 30

    # Default timeout to wait for a response when executing commands
    EXECUTE_TIMEOUT_SECS = 8

    def __init__(self, host: str, port: int):
        AsyncHelper.__init__(self)
        self._host = host
        self._port = port
        self._password = ''
        self._transport = None
        self._is_connected = False
        self._recv_buffer = ""
        self._executing = dict()
        self._time_last_data = time.time()

        self._on_connection_made = None
        self._on_connection_lost = None
        self._on_response = None
        self._on_device_event = None
        self._on_contact_id = None

    #
    # PROPERTIES
    #

    @property
    def host(self) -> str:
        """Host name or IP address for the LifeSOS ethernet interface."""
        return self._host

    @property
    def is_connected(self) -> bool:
        """True if client is connected to server; otherwise, False."""
        return self._is_connected

    @property
    def password(self) -> str:
        """Control password, if one has been assigned on the base unit."""
        return self._password

    @password.setter
    def password(self, password: str) -> None:
        self._password = password

    @property
    def port(self) -> int:
        """Port number for the LifeSOS ethernet interface."""
        return self._port

    #
    # EVENTS
    #

    @property
    def on_connection_made(self) -> Callable[['Client'], None]:
        """If implemented, called after a connection has been made."""
        return self._on_connection_made

    @on_connection_made.setter
    def on_connection_made(self, func: Callable[['Client'], None]) -> None:
        """
        Define the connection made callback implementation.

        Expected signature is:
            connection_made_callback(client)

        client:     the client instance for this callback
        """
        self._on_connection_made = func

    @property
    def on_connection_lost(self) -> Callable[['Client'], None]:
        """If implemented, called after a connection has been lost."""
        return self._on_connection_lost

    @on_connection_lost.setter
    def on_connection_lost(self, func: Callable[['Client', Exception], None]) -> None:
        """
        Define the connection lost callback implementation.

        Expected signature is:
            connection_lost_callback(client, exception)

        client:     the client instance for this callback
        exception:  an exception object if connection was aborted, or None
                    if closed normally.
        """
        self._on_connection_lost = func

    @property
    def on_response(self) -> Callable[['Client', Response, Command], None]:
        """If implemented, called when a response has been received."""
        return self._on_response

    @on_response.setter
    def on_response(self, func: Callable[['Client', Response, Command], None]) -> None:
        """
        Define the response callback implementation.

        Expected signature is:
            response_callback(client, response, command)

        client:     the client instance for this callback
        response:   the response that was received
        command:    the command instance specified on call to execute method,
                    or None if response due to a command from another client
        """
        self._on_response = func

    @property
    def on_device_event(self) -> Callable[['Client', DeviceEvent], None]:
        """If implemented, called when a device event has been received."""
        return self._on_device_event

    @on_device_event.setter
    def on_device_event(self, func: Callable[['Client', DeviceEvent], None]) -> None:
        """
        Define the device event callback implementation.

        Expected signature is:
            device_event_callback(client, device_event)

        client:         the client instance for this callback
        device_event:   info for the device event
        """
        self._on_device_event = func

    @property
    def on_contact_id(self) -> Callable[['Client', ContactID], None]:
        """If implemented, called when a ContactID message has been received."""
        return self._on_contact_id

    @on_contact_id.setter
    def on_contact_id(self, func: Callable[['Client', ContactID], None]) -> None:
        """
        Define the ContactID event callback implementation.

        Expected signature is:
            connect_id_callback(client, contact_id)

        client:         the client instance for this callback
        contact_id:     message using the Ademco ® Contact ID protocol.
        """
        self._on_contact_id = func

    #
    # METHODS - Public
    #

    async def async_open(self) -> None:
        """Opens connection to the LifeSOS ethernet interface."""

        await self._loop.create_connection(
            lambda: self,
            self._host,
            self._port)

        # Create task to ensure connection is alive
        self.create_task(self._async_ensure_alive, Client.ENSURE_ALIVE_SECS)

    def close(self) -> None:
        """Closes connection to the LifeSOS ethernet interface."""

        self.cancel_pending_tasks()

        _LOGGER.debug("Disconnected")
        self._transport.close()
        self._is_connected = False

    async def async_execute(self, command: Command, password: str = '',
                            timeout: int = EXECUTE_TIMEOUT_SECS) -> Response:
        """
        Execute a command and return response.

        command:    the command instance to be executed
        password:   if specified, will be used to execute this command (overriding any
                    global password that may have been assigned to the client property)
        timeout:    maximum number of seconds to wait for a response
        """
        if not self._is_connected:
            raise ConnectionError("Client is not connected to the server")
        state: Dict[str, Any] = {
            'command': command,
            'event': asyncio.Event(loop=self._loop)}
        self._executing[command.name] = state
        try:
            self._send(command, password)
            await asyncio.wait_for(state['event'].wait(), timeout)
            return state['response']
        finally:
            self._executing[command.name] = None

    #
    # METHODS - Private / Internal
    #

    async def _async_ensure_alive(self, interval: int) -> None:
        # Sends a no-op when nothing has been sent or received over the
        # connection for some time, to ensure it is still functional.
        while True:
            wait = max(interval - int(time.time() - self._time_last_data), 1)
            await asyncio.sleep(wait, loop=self._loop)
            if (time.time() - self._time_last_data) > interval:
                self._send(NoOpCommand())

    def _send(self, command: Command, password: str = '') -> None:
        # When no password specified on this call, use global password
        if password == '':
            password = self._password

        # Update data transfer timestamp
        self._time_last_data = time.time()

        # Write command to the stream
        command_text = command.format(password)
        self._transport.write(command_text.encode('ascii'))

        # Log data sent for diagnostics (hide the password though)
        command_hidepwd = command.format(''.ljust(len(password), '*'))
        _LOGGER.debug("DataSent: %s", command_hidepwd)

    def connection_made(self, transport):
        _LOGGER.debug("Connected")
        self._transport = transport
        self._is_connected = True
        self._recv_buffer = ""
        self._time_last_data = time.time()

        if self._on_connection_made:
            self._on_connection_made(self)

    def connection_lost(self, exc):
        if not exc:
            return

        _LOGGER.debug("ConnectionLost")
        self.cancel_pending_tasks()
        self._transport.close()
        self._is_connected = False

        if self._on_connection_lost:
            self._on_connection_lost(self, exc)

    def data_received(self, data):
        if not data:
            return

        self._time_last_data = time.time()

        # We should only receive ASCII text. Anything that doesn't decode is
        # garbage; a sign the user may have a faulty cable between the base
        # unit and the serial-ethernet adapter (this happened to me!)

        try:
            recv_chars = data.decode('ascii')
        except UnicodeDecodeError:
            _LOGGER.error("DataReceived: Data has bytes that cannot be decoded to ASCII: %s", data)
            return
        _LOGGER.debug("DataReceived: %s", recv_chars.replace('\n', '\\n').replace('\r', '\\r'))

        # Data received will have CR/LF somewhat randomly at either the start or end
        # of each message. To deal with this, we'll append it to a running buffer and then
        # use every portion terminated by either character (ignoring blank strings).

        self._recv_buffer += recv_chars
        lines = self._recv_buffer.splitlines()
        last_line = lines[len(lines) - 1]
        if last_line and self._recv_buffer.endswith(last_line):
            # Last line with no CR/LF; keep in buffer for next call
            self._recv_buffer = last_line
            lines.pop(len(lines) - 1)
        else:
            self._recv_buffer = ""
        for line in lines:
            if not line:
                continue

            # Handle responses; these are given in response to a command issued, either
            # by us or another client (if multiple connections enabled on adapter)
            if line.startswith(MARKER_START) and line.endswith(MARKER_END):
                try:
                    response = Response.parse(line)
                except Exception: # pylint: disable=broad-except
                    _LOGGER.error("Failed to parse response", exc_info=True)
                    continue
                if response:
                    _LOGGER.debug(response)
                    state = self._executing.get(response.command_name)
                    if state:
                        command = state['command']
                        state['response'] = response
                        state['event'].set()
                    else:
                        command = None

                    if self._on_response:
                        self._on_response(self, response, command)

            # Handle device events; eg. sensor triggered, low battery, etc...
            elif line.startswith('MINPIC='):
                try:
                    device_event = DeviceEvent(line)
                except Exception: # pylint: disable=broad-except
                    _LOGGER.error("Failed to parse device event", exc_info=True)
                    continue
                _LOGGER.debug(device_event)

                if self._on_device_event:
                    self._on_device_event(self, device_event)

            # Events from devices that haven't been enrolled, as well as a
            # display event from the base unit providing details to be shown.
            # Ignoring them as we have no interest in either.
            elif line.startswith('XINPIC='):
                # try:
                #     device_event = DeviceEvent(line)
                # except Exception:
                #     _LOGGER.error("Failed to parse device event", exc_info=True)
                #     continue
                # _LOGGER.debug(device_event)
                continue

            # Ademco ® Contact ID protocol
            elif line.startswith('(') and line.endswith(')'):
                try:
                    contact_id = ContactID(line[1:len(line)-1])
                except Exception: # pylint: disable=broad-except
                    _LOGGER.error("Failed to parse ContactID", exc_info=True)
                    continue
                _LOGGER.debug(contact_id)

                if self._on_contact_id:
                    self._on_contact_id(self, contact_id)

            # New sensor log entry; superfluous given device events already
            # provide us with this information, so just ignore them
            elif line.startswith('[' + CMD_SENSOR_LOG) and line.endswith(']'):
                continue

            # Failure to trigger an X10 switch
            elif line == 'X10 ERR':
                continue

            # Any unrecognised messages; ignore them too...
            else:
                continue
