# Project metadata
PROJECT_NAME = 'lifesospy'
PROJECT_DESCRIPTION = "Provides an interface to LifeSOS alarm systems."
PROJECT_VERSION = '0.6.0'
__version__ = PROJECT_VERSION

# Command names
CMD_CLEAR_STATUS = 'l5'
CMD_DATETIME = 'dt'
CMD_DEVBYIDX_PREFIX = 'k'
CMD_DEVICE_PREFIX = 'i'
CMD_ENTRY_DELAY = 'l1'
CMD_EVENT_LOG = 'ev'
CMD_EXIT_DELAY = 'l0'
CMD_OPMODE = 'n0'
CMD_ROMVER = 'vn'
CMD_SENSOR_LOG = 'et'
CMD_SWITCH_PREFIX = 's'

# Actions that can be performed by a command
ACTION_NONE = ''
ACTION_GET = '?'
ACTION_SET = 's'
ACTION_ADD = 'l'
ACTION_DEL = 'k'

# Message attributes
MA_NONE = 0x00
MA_TX3AC_10A = 0x01
MA_TX3AC_100A = 0x02

# Markers used at the start and end of commands/responses
MARKER_START = '!'
MARKER_END = '&'

# Text appended to response when base unit reports error
RESPONSE_ERROR = 'no'
