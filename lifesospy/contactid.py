from enum import IntEnum

class ContactID(object):
    """Represents a message using the Ademco ® Contact ID protocol."""

    def __init__(self, text):
        if len(text) != 16:
            raise ValueError("ContactID message length is invalid.")

        # Verify checksum
        check_val = 0
        for c in text:
            check_digit = int(c, 16)
            check_val += (check_digit if not check_digit == 0 else 10)
        if check_val % 15 != 0:
            raise ValueError("ContactID message checksum failure.")

        self._account_number = int(text[0:4], 16)
        self._message_type = int(text[4:6], 16)
        if not self._message_type in [0x18, 0x98]:
            raise ValueError("ContactID message type is invalid.")
        self._event_qualifier_value = int(text[6:7], 16)
        self._event_code = int(text[7:10], 16)
        self._partition = int(text[10:12], 16)
        self._zone_user = int(text[12:15], 16)
        self._checksum = int(text[15:16], 16)

        if EventQualifier.has_value(self._event_qualifier_value):
            self._event_qualifier = EventQualifier(self._event_qualifier_value)
        else:
            self._event_qualifier = None

        event_code = EventCodes.get(self._event_code)
        if event_code is not None:
            self._event_description = event_code['description']
            self._is_user = event_code['is_user']
        else:
            self._event_description = None
            self._is_user = None

    @property
    def account_number(self):
        return self._account_number

    @property
    def message_type(self):
        return self._message_type

    @property
    def event_qualifier_value(self):
        return self._event_qualifier_value

    @property
    def event_qualifier(self):
        return self._event_qualifier

    @property
    def event_code(self):
        return self._event_code

    @property
    def event_description(self):
        return self._event_description

    @property
    def is_user(self):
        return self._is_user

    @property
    def partition(self):
        return self._partition

    @property
    def zone_user(self):
        return self._zone_user

    @property
    def checksum(self):
        return self._checksum

    def __str__(self):
        return "Account {0:04x}, {1} {2:03x} ({3}), Partition {4:02x}, {5} {6:03x}".\
            format(self._account_number,
                   self._event_qualifier_value if not self._event_qualifier else self._event_qualifier.name,
                   self._event_code,
                   "Unknown" if not self._event_description else self._event_description,
                   self._partition,
                   "Zone" if not self._is_user else "User",
                   self._zone_user)

class EventQualifier(IntEnum):
    Event = 0x1
    Restore = 0x3
    Repeat = 0x6

    @classmethod
    def has_value(cls, value):
        return any(value == item.value for item in cls)

EventCodes = {

    # ALARMS

    # Medical Alarms –100
    0x100: { 'description': "Medical", 'is_user': False },
    0x101: { 'description': "Personal Emergency", 'is_user': False },
    0x102: { 'description': "Fail to report in", 'is_user': False },

    # Fire Alarms –110
    0x110: { 'description': "Fire", 'is_user': False },
    0x111: { 'description': "Smoke", 'is_user': False },
    0x112: { 'description': "Combustion", 'is_user': False },
    0x113: { 'description': "Water flow", 'is_user': False },
    0x114: { 'description': "Heat", 'is_user': False },
    0x115: { 'description': "Pull Station", 'is_user': False },
    0x116: { 'description': "Duct", 'is_user': False },
    0x117: { 'description': "Flame", 'is_user': False },
    0x118: { 'description': "Near Alarm", 'is_user': False },

    # Panic Alarms –120
    0x120: { 'description': "Panic", 'is_user': False },
    0x121: { 'description': "Duress", 'is_user': True },
    0x122: { 'description': "Silent", 'is_user': False },
    0x123: { 'description': "Audible", 'is_user': False },
    0x124: { 'description': "Duress – Access granted", 'is_user': False },
    0x125: { 'description': "Duress – Egress granted", 'is_user': False },

    # Burglar Alarms –130
    0x130: { 'description': "Burglary", 'is_user': False },
    0x131: { 'description': "Perimeter", 'is_user': False },
    0x132: { 'description': "Interior", 'is_user': False },
    0x133: { 'description': "24 Hour (Safe)", 'is_user': False },
    0x134: { 'description': "Entry/Exit", 'is_user': False },
    0x135: { 'description': "Day/night", 'is_user': False },
    0x136: { 'description': "Outdoor", 'is_user': False },
    0x137: { 'description': "Tamper", 'is_user': False },
    0x138: { 'description': "Near alarm", 'is_user': False },
    0x139: { 'description': "Intrusion Verifier", 'is_user': False },

    # General Alarm – 140
    0x140: { 'description': "General Alarm", 'is_user': False },
    0x141: { 'description': "Polling loop open", 'is_user': False },
    0x142: { 'description': "Polling loop short", 'is_user': False },
    0x143: { 'description': "Expansion module failure", 'is_user': False },
    0x144: { 'description': "Sensor tamper", 'is_user': False },
    0x145: { 'description': "Expansion module tamper", 'is_user': False },
    0x146: { 'description': "Silent Burglary", 'is_user': False },
    0x147: { 'description': "Sensor Supervision Failure", 'is_user': False },

    # 24 Hour Non-Burglary - 150 and 160
    0x150: { 'description': "24 Hour Non-Burglary", 'is_user': False },
    0x151: { 'description': "Gas detected", 'is_user': False },
    0x152: { 'description': "Refrigeration", 'is_user': False },
    0x153: { 'description': "Loss of heat", 'is_user': False },
    0x154: { 'description': "Water Leakage", 'is_user': False },
    0x155: { 'description': "Foil Break", 'is_user': False },
    0x156: { 'description': "Day Trouble", 'is_user': False },
    0x157: { 'description': "Low bottled gas level", 'is_user': False },
    0x158: { 'description': "High temp", 'is_user': False },
    0x159: { 'description': "Low temp", 'is_user': False },
    0x161: { 'description': "Loss of air flow", 'is_user': False },
    0x162: { 'description': "Carbon Monoxide detected", 'is_user': False },
    0x163: { 'description': "Tank level", 'is_user': False },

    # SUPERVISORY

    # Fire Supervisory - 200 and 210
    0x200: { 'description': "Fire Supervisory", 'is_user': False },
    0x201: { 'description': "Low water pressure", 'is_user': False },
    0x202: { 'description': "Low CO2", 'is_user': False },
    0x203: { 'description': "Gate valve sensor", 'is_user': False },
    0x204: { 'description': "Low water level", 'is_user': False },
    0x205: { 'description': "Pump activated", 'is_user': False },
    0x206: { 'description': "Pump failure", 'is_user': False },

    # TROUBLES

    # System Troubles -300 and 310
    0x300: { 'description': "System Trouble", 'is_user': False },
    0x301: { 'description': "AC Loss", 'is_user': False },
    0x302: { 'description': "Low system battery", 'is_user': False },
    0x303: { 'description': "RAM Checksum bad", 'is_user': False },
    0x304: { 'description': "ROM checksum bad", 'is_user': False },
    0x305: { 'description': "System reset", 'is_user': False },
    0x306: { 'description': "Panel programming changed", 'is_user': False },
    0x307: { 'description': "Self-test failure", 'is_user': False },
    0x308: { 'description': "System shutdown", 'is_user': False },
    0x309: { 'description': "Battery test failure", 'is_user': False },
    0x310: { 'description': "Ground fault", 'is_user': False },
    0x311: { 'description': "Battery Missing/Dead", 'is_user': False },
    0x312: { 'description': "Power Supply Overcurrent", 'is_user': False },
    0x313: { 'description': "Engineer Reset", 'is_user': True },

    # Sounder / Relay Troubles -320
    0x320: { 'description': "Sounder/Relay", 'is_user': False },
    0x321: { 'description': "Bell 1", 'is_user': False },
    0x322: { 'description': "Bell 2", 'is_user': False },
    0x323: { 'description': "Alarm relay", 'is_user': False },
    0x324: { 'description': "Trouble relay", 'is_user': False },
    0x325: { 'description': "Reversing relay", 'is_user': False },
    0x326: { 'description': "Notification Appliance Ckt. # 3", 'is_user': False },
    0x327: { 'description': "Notification Appliance Ckt. #4", 'is_user': False },

    # System Peripheral Trouble -330 and 340
    0x330: { 'description': "System Peripheral trouble", 'is_user': False },
    0x331: { 'description': "Polling loop open", 'is_user': False },
    0x332: { 'description': "Polling loop short", 'is_user': False },
    0x333: { 'description': "Expansion module failure", 'is_user': False },
    0x334: { 'description': "Repeater failure", 'is_user': False },
    0x335: { 'description': "Local printer out of paper", 'is_user': False },
    0x336: { 'description': "Local printer failure", 'is_user': False },
    0x337: { 'description': "Exp. Module DC Loss", 'is_user': False },
    0x338: { 'description': "Exp. Module Low Batt.", 'is_user': False },
    0x339: { 'description': "Exp. Module Reset", 'is_user': False },
    0x341: { 'description': "Exp. Module Tamper", 'is_user': False },
    0x342: { 'description': "Exp. Module AC Loss", 'is_user': False },
    0x343: { 'description': "Exp. Module self-test fail", 'is_user': False },
    0x344: { 'description': "RF Receiver Jam Detect", 'is_user': False },

    # Communication Troubles -350 and 360
    0x350: { 'description': "Communication trouble", 'is_user': False },
    0x351: { 'description': "Telco 1 fault", 'is_user': False },
    0x352: { 'description': "Telco 2 fault", 'is_user': False },
    0x353: { 'description': "Long Range Radio xmitter fault", 'is_user': False },
    0x354: { 'description': "Failure to communicate event", 'is_user': False },
    0x355: { 'description': "Loss of Radio supervision", 'is_user': False },
    0x356: { 'description': "Loss of central polling", 'is_user': False },
    0x357: { 'description': "Long Range Radio VSWR problem", 'is_user': False },

    # Protection Loop -370
    0x370: { 'description': "Protection loop", 'is_user': False },
    0x371: { 'description': "Protection loop open", 'is_user': False },
    0x372: { 'description': "Protection loop short", 'is_user': False },
    0x373: { 'description': "Fire trouble", 'is_user': False },
    0x374: { 'description': "Exit error alarm (zone)", 'is_user': False },
    0x375: { 'description': "Panic zone trouble", 'is_user': False },
    0x376: { 'description': "Hold-up zone trouble", 'is_user': False },
    0x377: { 'description': "Swinger Trouble", 'is_user': False },
    0x378: { 'description': "Cross-zone Trouble", 'is_user': False },

    # Sensor Trouble -380
    0x380: { 'description': "Sensor trouble", 'is_user': False },
    0x381: { 'description': "Loss of supervision - RF", 'is_user': False },
    0x382: { 'description': "Loss of supervision - RPM", 'is_user': False },
    0x383: { 'description': "Sensor tamper", 'is_user': False },
    0x384: { 'description': "RF low battery", 'is_user': False },
    0x385: { 'description': "Smoke detector Hi sensitivity", 'is_user': False },
    0x386: { 'description': "Smoke detector Low sensitivity", 'is_user': False },
    0x387: { 'description': "Intrusion detector Hi sensitivity", 'is_user': False },
    0x388: { 'description': "Intrusion detector Low sensitivity", 'is_user': False },
    0x389: { 'description': "Sensor self-test failure", 'is_user': False },
    0x391: { 'description': "Sensor Watch trouble", 'is_user': False },
    0x392: { 'description': "Drift Compensation Error", 'is_user': False },
    0x393: { 'description': "Maintenance Alert", 'is_user': False },

    # OPEN/CLOSE/REMOTE ACCESS

    # Open/Close -400, 440,450
    0x400: { 'description': "Open/Close", 'is_user': True },
    0x401: { 'description': "O/C by user", 'is_user': True },
    0x402: { 'description': "Group O/C", 'is_user': True },
    0x403: { 'description': "Automatic O/C", 'is_user': True },
    0x404: { 'description': "Late to O/C  (Note: use 453, 454 instead )", 'is_user': True },
    0x405: { 'description': "Deferred O/C (Obsolete- do not use )", 'is_user': True },
    0x406: { 'description': "Cancel", 'is_user': True },
    0x407: { 'description': "Remote arm/disarm", 'is_user': True },
    0x408: { 'description': "Quick arm", 'is_user': True },
    0x409: { 'description': "Keyswitch O/C", 'is_user': True },
    0x441: { 'description': "Armed STAY", 'is_user': True },
    0x442: { 'description': "Keyswitch Armed STAY", 'is_user': True },
    0x450: { 'description': "Exception O/C", 'is_user': True },
    0x451: { 'description': "Early O/C", 'is_user': True },
    0x452: { 'description': "Late O/C", 'is_user': True },
    0x453: { 'description': "Failed to Open", 'is_user': True },
    0x454: { 'description': "Failed to Close", 'is_user': True },
    0x455: { 'description': "Auto-arm Failed", 'is_user': True },
    0x456: { 'description': "Partial Arm", 'is_user': True },
    0x457: { 'description': "Exit Error (user)", 'is_user': True },
    0x458: { 'description': "User on Premises", 'is_user': True },
    0x459: { 'description': "Recent Close", 'is_user': True },
    0x461: { 'description': "Wrong Code Entry", 'is_user': False },
    0x462: { 'description': "Legal Code Entry", 'is_user': True },
    0x463: { 'description': "Re-arm after Alarm", 'is_user': True },
    0x464: { 'description': "Auto-arm Time Extended", 'is_user': True },
    0x465: { 'description': "Panic Alarm Reset", 'is_user': False },
    0x466: { 'description': "Service On/Off Premises", 'is_user': True },

    # Remote Access –410
    0x411: { 'description': "Callback request made", 'is_user': True },
    0x412: { 'description': "Successful download/access", 'is_user': True },
    0x413: { 'description': "Unsuccessful access", 'is_user': True },
    0x414: { 'description': "System shutdown command received", 'is_user': True },
    0x415: { 'description': "Dialer shutdown command received", 'is_user': True },
    0x416: { 'description': "Successful Upload", 'is_user': False },

    # Access control –420,430
    0x421: { 'description': "Access denied", 'is_user': True },
    0x422: { 'description': "Access report by user", 'is_user': True },
    0x423: { 'description': "Forced Access", 'is_user': False },
    0x424: { 'description': "Egress Denied", 'is_user': True },
    0x425: { 'description': "Egress Granted", 'is_user': True },
    0x426: { 'description': "Access Door propped open", 'is_user': False },
    0x427: { 'description': "Access point Door Status Monitor trouble", 'is_user': False },
    0x428: { 'description': "Access point Request To Exit trouble", 'is_user': False },
    0x429: { 'description': "Access program mode entry", 'is_user': True },
    0x430: { 'description': "Access program mode exit", 'is_user': True },
    0x431: { 'description': "Access threat level change", 'is_user': True },
    0x432: { 'description': "Access relay/trigger fail", 'is_user': False },
    0x433: { 'description': "Access RTE shunt", 'is_user': False },
    0x434: { 'description': "Access DSM shunt", 'is_user': False },

    # BYPASSES / DISABLES

    # System Disables -500 and 510
    0x501: { 'description': "Access reader disable", 'is_user': False },

    # Sounder / Relay Disables -520
    0x520: { 'description': "Sounder/Relay Disable", 'is_user': False },
    0x521: { 'description': "Bell 1 disable", 'is_user': False },
    0x522: { 'description': "Bell 2 disable", 'is_user': False },
    0x523: { 'description': "Alarm relay disable", 'is_user': False },
    0x524: { 'description': "Trouble relay disable", 'is_user': False },
    0x525: { 'description': "Reversing relay disable", 'is_user': False },
    0x526: { 'description': "Notification Appliance Ckt. # 3 disable", 'is_user': False },
    0x527: { 'description': "Notification Appliance Ckt. # 4 disable", 'is_user': False },

    # System Peripheral Disables -530 and 540
    0x531: { 'description': "Module Added", 'is_user': False },
    0x532: { 'description': "Module Removed", 'is_user': False },

    # Communication Disables -550 and 560
    0x551: { 'description': "Dialer disabled", 'is_user': False },
    0x552: { 'description': "Radio transmitter disabled", 'is_user': False },
    0x553: { 'description': "Remote Upload/Download disabled", 'is_user': False },

    # Bypasses –570
    0x570: { 'description': "Zone/Sensor bypass", 'is_user': False },
    0x571: { 'description': "Fire bypass", 'is_user': False },
    0x572: { 'description': "24 Hour zone bypass", 'is_user': False },
    0x573: { 'description': "Burg. Bypass", 'is_user': False },
    0x574: { 'description': "Group bypass", 'is_user': True },
    0x575: { 'description': "Swinger bypass", 'is_user': False },
    0x576: { 'description': "Access zone shunt", 'is_user': False },
    0x577: { 'description': "Access point bypass", 'is_user': False },

    # TEST / MISC.

    # Test/Misc. –600, 610
    0x601: { 'description': "Manual trigger test report", 'is_user': False },
    0x602: { 'description': "Periodic test report", 'is_user': False },
    0x603: { 'description': "Periodic RF transmission", 'is_user': False },
    0x604: { 'description': "Fire test", 'is_user': True },
    0x605: { 'description': "Status report to follow", 'is_user': False },
    0x606: { 'description': "Listen-in to follow", 'is_user': False },
    0x607: { 'description': "Walk test mode", 'is_user': True },
    0x608: { 'description': "Periodic test - System Trouble Present", 'is_user': False },
    0x609: { 'description': "Video Xmitter active", 'is_user': False },
    0x611: { 'description': "Point tested OK", 'is_user': False },
    0x612: { 'description': "Point not tested", 'is_user': False },
    0x613: { 'description': "Intrusion Zone Walk Tested", 'is_user': False },
    0x614: { 'description': "Fire Zone Walk Tested", 'is_user': False },
    0x615: { 'description': "Panic Zone Walk Tested", 'is_user': False },
    0x616: { 'description': "Service Request", 'is_user': False },

    # Event Log –620
    0x621: { 'description': "Event Log reset", 'is_user': False },
    0x622: { 'description': "Event Log 50% full", 'is_user': False },
    0x623: { 'description': "Event Log 90% full", 'is_user': False },
    0x624: { 'description': "Event Log overflow", 'is_user': False },
    0x625: { 'description': "Time/Date reset", 'is_user': True },
    0x626: { 'description': "Time/Date inaccurate", 'is_user': False },
    0x627: { 'description': "Program mode entry", 'is_user': False },
    0x628: { 'description': "Program mode exit", 'is_user': False },
    0x629: { 'description': "32 Hour Event log marker", 'is_user': False },

    # Scheduling –630
    0x630: { 'description': "Schedule change", 'is_user': False },
    0x631: { 'description': "Exception schedule change", 'is_user': False },
    0x632: { 'description': "Access schedule change", 'is_user': False },

    # Personnel Monitoring -640
    0x641: { 'description': "Senior Watch Trouble", 'is_user': False },
    0x642: { 'description': "Latch-key Supervision", 'is_user': True },

    # Misc. -650
    0x651: { 'description': "Reserved for Ademco Use", 'is_user': False },
    0x652: { 'description': "Reserved for Ademco Use", 'is_user': True },
    0x653: { 'description': "Reserved for Ademco Use", 'is_user': True },
    0x654: { 'description': "System Inactivity", 'is_user': False }

}
