"""
This module contains the Client class.
"""

import logging
from lifesospy.protocol import Protocol

_LOGGER = logging.getLogger(__name__)


class Client(Protocol):
    """
    Provides connectivity to a LifeSOS ethernet adapter that is configured
    in TCP Server mode.

    Your application can use the Client or Server class for direct access
    to LifeSOS, or alternatively use the BaseUnit class to provide management
    and higher level access.
    """

    def __init__(self, host: str, port: int):
        super().__init__()
        self._host = host
        self._port = port

    #
    # PROPERTIES
    #

    @property
    def host(self) -> str:
        """Host name or IP address for the LifeSOS server."""
        return self._host

    @property
    def port(self) -> int:
        """Port number for the LifeSOS server."""
        return self._port

    #
    # METHODS - Public
    #

    async def async_open(self) -> None:
        """Opens connection to the LifeSOS ethernet interface."""

        await self._loop.create_connection(
            lambda: self,
            self._host,
            self._port)
