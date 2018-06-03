import asyncio
import logging
import threading
import time

from lifesospy.command import *
from lifesospy.const import *
from lifesospy.contactid import ContactID
from lifesospy.deviceevent import DeviceEvent
from lifesospy.enums import *
from lifesospy.response import Response

_LOGGER = logging.getLogger(__name__)

class Client(asyncio.Protocol):
    """Provides connectivity to the LifeSOS ethernet interface."""

    # Ensure connection still alive when no data sent/recieved after this many seconds
    ENSURE_ALIVE_SECS = 30

    # Default timeout to wait for a response when executing commands.
    EXECUTE_TIMEOUT_SECS = 10

    # Attempt reconnection after waiting this many seconds
    RETRY_CONNECTION_SECS = 30

    def __init__(self, host, port, event_loop):
        self._host = host
        self._port = port
        self._event_loop = event_loop
        self._password = ''
        self._transport = None
        self._shutdown = False
        self._recv_buffer = ""
        self._executing = dict()
        self._time_last_data = time.time()
        self._on_connected = None
        self._on_response = None
        self._on_device_event = None
        self._on_contact_id = None
        self._in_callback = threading.Lock()
        self._callback_mutex = threading.RLock()

    #
    # PROPERTIES
    #

    @property
    def host(self):
        """Host name or IP address for the LifeSOS ethernet interface."""
        return self._host

    @property
    def port(self):
        """Port number for the LifeSOS ethernet interface."""
        return self._port

    @property
    def event_loop(self):
        """Event loop for asyncio."""
        return self._event_loop

    @property
    def password(self):
        """Control password, if one has been assigned on the base unit."""
        return self._password

    @password.setter
    def password(self, password):
        self._password = password

    @property
    def on_connected(self):
        """If implemented, called after a connection has been established."""
        return self._on_connected

    @on_connected.setter
    def on_connected(self, func):
        """
        Define the connected callback implementation.

        Expected signature is:
            connected_callback(client)

        client:     the client instance for this callback
        """
        with self._callback_mutex:
            self._on_connected = func

    @property
    def on_response(self):
        """If implemented, called when a response has been received."""
        return self._on_response

    @on_response.setter
    def on_response(self, func):
        """
        Define the response callback implementation.

        Expected signature is:
            response_callback(client, response, command)

        client:     the client instance for this callback
        response:   the response that was received
        command:    the command instance specified on call to execute method,
                    or None if response due to a command from another client
        """
        with self._callback_mutex:
            self._on_response = func

    @property
    def on_device_event(self):
        """If implemented, called when a device event has been received."""
        return self._on_device_event

    @on_device_event.setter
    def on_device_event(self, func):
        """
        Define the device event callback implementation.

        Expected signature is:
            device_event_callback(client, device_event)

        client:         the client instance for this callback
        device_event:   info for the device event
        """
        with self._callback_mutex:
            self._on_device_event = func

    @property
    def on_contact_id(self):
        """If implemented, called when a ContactID message has been received."""
        return self._on_contact_id

    @on_contact_id.setter
    def on_contact_id(self, func):
        """
        Define the ContactID event callback implementation.

        Expected signature is:
            connect_id_callback(client, contact_id)

        client:         the client instance for this callback
        contact_id:     message using the Ademco ® Contact ID protocol.
        """
        with self._callback_mutex:
            self._on_contact_id = func

    #
    # METHODS - Public
    #

    def open(self):
        """Opens connection to the LifeSOS ethernet interface."""
        self._shutdown = False
        self._open()
        asyncio.ensure_future(self._ensure_alive(), loop=self._event_loop)

    def close(self):
        """Closes connection to the LifeSOS ethernet interface."""
        self._shutdown = True
        self._close()

    async def execute(self, command, timeout=EXECUTE_TIMEOUT_SECS):
        """Execute a command and return response."""
        state = {
            'command': command,
            'event': asyncio.Event(loop=self._event_loop)}
        self._executing[command.name] = state
        try:
            self._send(command)
            await asyncio.wait_for( state['event'].wait(), timeout)
            return state['response']
        finally:
            self._executing[command.name] = None

    #
    # METHODS - Private
    #

    def _open(self):
        asyncio.ensure_future(self._event_loop.create_connection(lambda: self, self._host, self._port), loop=self._event_loop)

    def _reconnect(self, delay):
        self._event_loop.call_later(delay, self._open)

    def _close(self):
        _LOGGER.debug("DISCONNECTED.")
        self._transport.close()

    async def _ensure_alive(self):
        # Sends a no-op when nothing has been sent or received over the
        # connection for some time, to ensure it is still functional.
        while not self._shutdown:
            wait = max(Client.ENSURE_ALIVE_SECS - int(time.time() - self._time_last_data), 1)
            await asyncio.sleep(wait, loop=self._event_loop)
            if (time.time() - self._time_last_data) > Client.ENSURE_ALIVE_SECS:
                self._send(NoOpCommand())

    def _send(self, command):
        self._time_last_data = time.time()
        command_text = command.format(self._password)
        self._transport.write(command_text.encode('ascii'))
        _LOGGER.debug("DATA SENT: %s", command_text)

    #
    # METHODS - Protocol overrides
    #

    def connection_made(self, transport):
        _LOGGER.debug("CONNECTED.")
        self._transport = transport
        self._recv_buffer = ""
        self._time_last_data = time.time()

        with self._callback_mutex:
            if self._on_connected:
                with self._in_callback:
                    self._on_connected(self)

    def connection_lost(self, exc):
        if not self._shutdown:
            _LOGGER.warning("LOST CONNECTION. Will retry in %s seconds...", Client.RETRY_CONNECTION_SECS)
            self._reconnect(Client.RETRY_CONNECTION_SECS)

    def data_received(self, data):
        if not data:
            return

        self._time_last_data = time.time()

        # We should only receive ASCII text. Anything that doesn't decode is
        # garbage; a sign the user may have a faulty cable between the base
        # unit and the serial-ethernet adapter (this happened to me!)

        try:
            recv_chars = data.decode('ascii')
        except UnicodeDecodeError as ex:
            _LOGGER.error("DATA RCVD: Data has bytes that cannot be decoded to ASCII: %s", data)
            return
        _LOGGER.debug("DATA RCVD: %s", recv_chars.replace('\n','\\n').replace('\r','\\r'))

        # Data received will have CR/LF somewhat randomly at either the start or end
        # of each message. To deal with this, we'll append it to a running buffer and then
        # use every portion terminated by either character (ignoring blank strings).

        self._recv_buffer += recv_chars
        lines = self._recv_buffer.splitlines()
        last_line = lines[len(lines) - 1]
        if len(last_line) > 0 and self._recv_buffer.endswith(last_line):
            # Last line with no CR/LF; keep in buffer for next call
            self._recv_buffer = last_line
            lines.pop(len(lines) - 1)
        else:
            self._recv_buffer = ""
        for line in lines:
            if len(line) == 0:
                continue

            # Handle responses; these are given in response to a command issued, either
            # by us or another client (if multiple connections enabled on adapter)
            if line.startswith(MARKER_START) and line.endswith(MARKER_END):
                try:
                    response = Response.parse(line)
                except Exception as ex:
                    _LOGGER.warning(ex)
                    continue
                if response:
                    _LOGGER.debug("RESPONSE: %s", response)
                    state = self._executing.get(response.command_name)
                    if state:
                        command = state['command']
                        state['response'] = response
                        state['event'].set()
                    else:
                        command = None

                    with self._callback_mutex:
                        if self._on_response:
                            with self._in_callback:
                                self._on_response(self, response, command)

            # Handle device events; eg. sensor triggered, low battery, etc...
            elif line.startswith('MINPIC='):
                try:
                    device_event = DeviceEvent(line)
                except Exception as ex:
                    _LOGGER.warning(ex)
                    continue
                _LOGGER.debug("EVENT: %s", device_event)

                with self._callback_mutex:
                    if self._on_device_event:
                        with self._in_callback:
                            self._on_device_event(self, device_event)

            # Not really sure what these are; appear to be events generated
            # periodically by base unit. Will ignore for now.
            elif line.startswith('XINPIC='):
                continue

            # Ademco ® Contact ID protocol
            elif line.startswith('(') and line.endswith(')'):
                try:
                    contact_id = ContactID(line[1:len(line)-1])
                except Exception as ex:
                    _LOGGER.warning(ex)
                    continue
                _LOGGER.debug("CONTACTID: %s", contact_id)

                with self._callback_mutex:
                    if self._on_contact_id:
                        with self._in_callback:
                            self._on_contact_id(self, contact_id)

            # Any unrecognised messages; ignore them too...
            else:
                continue
