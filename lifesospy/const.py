from collections import OrderedDict
from lifesospy.devicecategory import DeviceCategory

# Markers used at the start and end of commands/responses
MARKER_START = '!'
MARKER_END = '&'

# Command names
CMD_CLEAR_STATUS = 'l5'
CMD_DATETIME = 'dt'
CMD_DEVBYIDX_PREFIX = 'k'
CMD_DEVBYZON_PREFIX = 'i'
CMD_ENTRY_DELAY = 'l1'
CMD_EXIT_DELAY = 'l0'
CMD_OPMODE = 'n0'
CMD_ROMVER = 'vn'

# Actions that can be performed by a command
ACTION_GET = '?'
ACTION_SET = 's'

# Device categories
DC_CONTROLLER = DeviceCategory('c', 'Controller', 32)
DC_BURGLAR = DeviceCategory('b', 'Burglar', 128)
DC_FIRE = DeviceCategory('f', 'Fire', 64)
DC_MEDICAL = DeviceCategory('m', 'Medical', 32)
DC_SPECIAL = DeviceCategory('e', 'Special', 32)
DC_BASEUNIT = DeviceCategory('z', 'Base Unit', None)
DC_ALL = [
    DC_CONTROLLER, DC_BURGLAR, DC_FIRE, DC_MEDICAL, DC_SPECIAL, DC_BASEUNIT]
DC_ALL_LOOKUP = OrderedDict()
for dc in DC_ALL:
    DC_ALL_LOOKUP[dc.id] = dc
