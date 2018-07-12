"""
This module contains the Server class.
"""

import logging
from typing import Optional
from lifesospy.protocol import Protocol

_LOGGER = logging.getLogger(__name__)


class Server(Protocol):
    """
    Provides connectivity to a LifeSOS ethernet adapter that is configured
    in TCP Client mode.

    Note that while multiple incoming connections are accepted, it is assumed
    that it will only be from a single LifeSOS ethernet adapter. There is no
    logic in this Server implementation to handle multiple devices.

    Your application can use the Client or Server class for direct access
    to LifeSOS, or alternatively use the BaseUnit class to provide management
    and higher level access.
    """

    def __init__(self, listen_port: int):
        super().__init__()
        self._listen_port = listen_port
        self._host = None
        self._port = None

    #
    # PROPERTIES
    #

    @property
    def host(self) -> Optional[str]:
        """Host name or IP address for the LifeSOS client."""
        return self._host

    @property
    def listen_port(self) -> int:
        """Port number we are listening on."""
        return self._listen_port

    @property
    def port(self) -> Optional[int]:
        """Port number for the LifeSOS client."""
        return self._port

    #
    # METHODS - Public
    #

    async def async_listen(self) -> None:
        """Listens for connection from the LifeSOS ethernet interface."""

        await self._loop.create_server(
            lambda: self,
            port=self._listen_port)

    #
    # METHODS - Private / Internal
    #

    def connection_made(self, transport):
        # Store remote host / port before passing to base class
        peername = transport.get_extra_info('peername')
        if peername:
            self._host = peername[0]
            self._port = peername[1]
        super().connection_made(transport)

    def connection_lost(self, exc):
        # Clear remote host / port before passing to base class
        self._host = None
        self._port = None
        super().connection_lost(exc)
