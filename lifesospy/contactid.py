from lifesospy.enums import (
    ContactIDEventQualifier as EventQualifier,
    ContactIDEventCode as EventCode)

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
        self._event_code_value = int(text[7:10], 16)
        self._partition = int(text[10:12], 16)
        self._zone_user = int(text[12:15], 16)
        self._checksum = int(text[15:16], 16)

        if EventQualifier.has_value(self._event_qualifier_value):
            self._event_qualifier = EventQualifier(self._event_qualifier_value)
        else:
            self._event_qualifier = None

        if EventCode.has_value(self._event_code_value):
            self._event_code = EventCode(self._event_code_value)
            self._event_attributes = CONTACT_ID_EVENT_ATTRIBUTES.get(self._event_code)
        else:
            self._event_code = None
            self._event_attributes = {}

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
    def event_code_value(self):
        return self._event_code_value

    @property
    def event_code(self):
        return self._event_code

    @property
    def event_attributes(self):
        return self._event_attributes

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
                   self._event_code_value,
                   "Unknown" if not self._event_attributes else self._event_attributes['description'],
                   self._partition,
                   "Zone" if not self._event_attributes['is_user'] else "User",
                   self._zone_user)

# Provides additional attributes for events
CONTACT_ID_EVENT_ATTRIBUTES = {

    # ALARMS

    # Medical Alarms -100
    EventCode.Medical: {
        'description': "Medical",
        'is_user': False},
    EventCode.PersonalEmergency: {
        'description': "Personal Emergency",
        'is_user': False},
    EventCode.FailToReportIn: {
        'description': "Fail to report in",
        'is_user': False},

    # Fire Alarms -110
    EventCode.Fire: {
        'description': "Fire",
        'is_user': False},
    EventCode.Smoke: {
        'description': "Smoke",
        'is_user': False},
    EventCode.Combustion: {
        'description': "Combustion",
        'is_user': False},
    EventCode.WaterFlow: {
        'description': "Water flow",
        'is_user': False},
    EventCode.Heat: {
        'description': "Heat",
        'is_user': False},
    EventCode.PullStation: {
        'description': "Pull Station",
        'is_user': False},
    EventCode.Duct: {
        'description': "Duct",
        'is_user': False},
    EventCode.Flame: {
        'description': "Flame",
        'is_user': False},
    EventCode.Fire_NearAlarm: {
        'description': "Near Alarm",
        'is_user': False},

    # Panic Alarms -120
    EventCode.Panic: {
        'description': "Panic",
        'is_user': False},
    EventCode.Duress: {
        'description': "Duress",
        'is_user': True},
    EventCode.Silent: {
        'description': "Silent",
        'is_user': False},
    EventCode.Audible: {
        'description': "Audible",
        'is_user': False},
    EventCode.Duress_AccessGranted: {
        'description': "Duress - Access granted",
        'is_user': False},
    EventCode.Duress_EgressGranted: {
        'description': "Duress - Egress granted",
        'is_user': False},

    # Burglar Alarms -130
    EventCode.Burglary: {
        'description': "Burglary",
        'is_user': False},
    EventCode.Perimeter: {
        'description': "Perimeter",
        'is_user': False},
    EventCode.Interior: {
        'description': "Interior",
        'is_user': False},
    EventCode.AlwaysOnBurglar: {
        'description': "24 Hour (Safe)",
        'is_user': False},
    EventCode.EntryExit: {
        'description': "Entry/Exit",
        'is_user': False},
    EventCode.DayNight: {
        'description': "Day/night",
        'is_user': False},
    EventCode.Outdoor: {
        'description': "Outdoor",
        'is_user': False},
    EventCode.Tamper: {
        'description': "Tamper",
        'is_user': False},
    EventCode.Burglar_NearAlarm: {
        'description': "Near alarm",
        'is_user': False},
    EventCode.IntrusionVerifier: {
        'description': "Intrusion Verifier",
        'is_user': False},

    # General Alarm - 140
    EventCode.GeneralAlarm: {
        'description': "General Alarm",
        'is_user': False},
    EventCode.PollingLoopOpen_Alarm: {
        'description': "Polling loop open",
        'is_user': False},
    EventCode.PollingLoopShort_Alarm: {
        'description': "Polling loop short",
        'is_user': False},
    EventCode.ExpansionModuleFailure_Alarm: {
        'description': "Expansion module failure",
        'is_user': False},
    EventCode.SensorTamper_Alarm: {
        'description': "Sensor tamper",
        'is_user': False},
    EventCode.ExpansionModuleTamper: {
        'description': "Expansion module tamper",
        'is_user': False},
    EventCode.SilentBurglary: {
        'description': "Silent Burglary",
        'is_user': False},
    EventCode.SensorSupervisionFailure: {
        'description': "Sensor Supervision Failure",
        'is_user': False},

    # 24 Hour Non-Burglary - 150 and 160
    EventCode.AlwaysOnNonBurglary: {
        'description': "24 Hour Non-Burglary",
        'is_user': False},
    EventCode.GasDetected: {
        'description': "Gas detected",
        'is_user': False},
    EventCode.Refrigeration: {
        'description': "Refrigeration",
        'is_user': False},
    EventCode.LossOfHeat: {
        'description': "Loss of heat",
        'is_user': False},
    EventCode.WaterLeakage: {
        'description': "Water Leakage",
        'is_user': False},
    EventCode.FoilBreak: {
        'description': "Foil Break",
        'is_user': False},
    EventCode.DayTrouble: {
        'description': "Day Trouble",
        'is_user': False},
    EventCode.LowBottledGasLevel: {
        'description': "Low bottled gas level",
        'is_user': False},
    EventCode.HighTemp: {
        'description': "High temp",
        'is_user': False},
    EventCode.LowTemp: {
        'description': "Low temp",
        'is_user': False},
    EventCode.LossOfAirFlow: {
        'description': "Loss of air flow",
        'is_user': False},
    EventCode.CarbonMonoxideDetected: {
        'description': "Carbon Monoxide detected",
        'is_user': False},
    EventCode.TankLevel: {
        'description': "Tank level",
        'is_user': False},

    # SUPERVISORY

    # Fire Supervisory - 200 and 210
    EventCode.FireSupervisory: {
        'description': "Fire Supervisory",
        'is_user': False},
    EventCode.LowWaterPressure: {
        'description': "Low water pressure",
        'is_user': False},
    EventCode.LowCO2: {
        'description': "Low CO2",
        'is_user': False},
    EventCode.GateValveSensor: {
        'description': "Gate valve sensor",
        'is_user': False},
    EventCode.LowWaterLevel: {
        'description': "Low water level",
        'is_user': False},
    EventCode.PumpActivated: {
        'description': "Pump activated",
        'is_user': False},
    EventCode.PumpFailure: {
        'description': "Pump failure",
        'is_user': False},

    # TROUBLES

    # System Troubles -300 and 310
    EventCode.SystemTrouble: {
        'description': "System Trouble",
        'is_user': False},
    EventCode.ACLoss: {
        'description': "AC Loss",
        'is_user': False},
    EventCode.LowSystemBattery: {
        'description': "Low system battery",
        'is_user': False},
    EventCode.RAMChecksumBad: {
        'description': "RAM Checksum bad",
        'is_user': False},
    EventCode.ROMChecksumBad: {
        'description': "ROM checksum bad",
        'is_user': False},
    EventCode.SystemReset: {
        'description': "System reset",
        'is_user': False},
    EventCode.PanelProgrammingChanged: {
        'description': "Panel programming changed",
        'is_user': False},
    EventCode.SelfTestFailure: {
        'description': "Self-test failure",
        'is_user': False},
    EventCode.SystemShutdown: {
        'description': "System shutdown",
        'is_user': False},
    EventCode.BatteryTestFailure: {
        'description': "Battery test failure",
        'is_user': False},
    EventCode.GroundFault: {
        'description': "Ground fault",
        'is_user': False},
    EventCode.BatteryMissingDead: {
        'description': "Battery Missing/Dead",
        'is_user': False},
    EventCode.PowerSupplyOvercurrent: {
        'description': "Power Supply Overcurrent",
        'is_user': False},
    EventCode.EngineerReset: {
        'description': "Engineer Reset",
        'is_user': True},

    # Sounder / Relay Troubles -320
    EventCode.SounderRelay: {
        'description': "Sounder/Relay",
        'is_user': False},
    EventCode.Bell1: {
        'description': "Bell 1",
        'is_user': False},
    EventCode.Bell2: {
        'description': "Bell 2",
        'is_user': False},
    EventCode.AlarmRelay: {
        'description': "Alarm relay",
        'is_user': False},
    EventCode.TroubleRelay: {
        'description': "Trouble relay",
        'is_user': False},
    EventCode.ReversingRelay: {
        'description': "Reversing relay",
        'is_user': False},
    EventCode.NotificationApplianceCkt3: {
        'description': "Notification Appliance Ckt. # 3",
        'is_user': False},
    EventCode.NotificationApplianceCkt4: {
        'description': "Notification Appliance Ckt. #4",
        'is_user': False},

    # System Peripheral Trouble -330 and 340
    EventCode.SystemPeripheralTrouble: {
        'description': "System Peripheral trouble",
        'is_user': False},
    EventCode.PollingLoopOpen_Trouble: {
        'description': "Polling loop open",
        'is_user': False},
    EventCode.PollingLoopShort_Trouble: {
        'description': "Polling loop short",
        'is_user': False},
    EventCode.ExpansionModuleFailure_Trouble: {
        'description': "Expansion module failure",
        'is_user': False},
    EventCode.RepeaterFailure: {
        'description': "Repeater failure",
        'is_user': False},
    EventCode.LocalPrinterOutOfPaper: {
        'description': "Local printer out of paper",
        'is_user': False},
    EventCode.LocalPrinterFailure: {
        'description': "Local printer failure",
        'is_user': False},
    EventCode.ExpModuleDCLoss: {
        'description': "Exp. Module DC Loss",
        'is_user': False},
    EventCode.ExpModuleLowBatt: {
        'description': "Exp. Module Low Batt.",
        'is_user': False},
    EventCode.ExpModuleReset: {
        'description': "Exp. Module Reset",
        'is_user': False},
    EventCode.ExpModuleTamper: {
        'description': "Exp. Module Tamper",
        'is_user': False},
    EventCode.ExpModuleACLoss: {
        'description': "Exp. Module AC Loss",
        'is_user': False},
    EventCode.ExpModuleSelfTestFail: {
        'description': "Exp. Module self-test fail",
        'is_user': False},
    EventCode.RFReceiverJamDetect: {
        'description': "RF Receiver Jam Detect",
        'is_user': False},

    # Communication Troubles -350 and 360
    EventCode.CommunicationTrouble: {
        'description': "Communication trouble",
        'is_user': False},
    EventCode.Telco1Fault: {
        'description': "Telco 1 fault",
        'is_user': False},
    EventCode.Telco2Fault: {
        'description': "Telco 2 fault",
        'is_user': False},
    EventCode.LongRangeRadioXmitterFault: {
        'description': "Long Range Radio xmitter fault",
        'is_user': False},
    EventCode.FailureToCommunicateEvent: {
        'description': "Failure to communicate event",
        'is_user': False},
    EventCode.LossOfRadioSupervision: {
        'description': "Loss of Radio supervision",
        'is_user': False},
    EventCode.LossOfCentralPolling: {
        'description': "Loss of central polling",
        'is_user': False},
    EventCode.LongRangeRadioVSWRProblem: {
        'description': "Long Range Radio VSWR problem",
        'is_user': False},

    # Protection Loop -370
    EventCode.ProtectionLoop: {
        'description': "Protection loop",
        'is_user': False},
    EventCode.ProtectionLoopOpen: {
        'description': "Protection loop open",
        'is_user': False},
    EventCode.ProtectionLoopShort: {
        'description': "Protection loop short",
        'is_user': False},
    EventCode.FireTrouble: {
        'description': "Fire trouble",
        'is_user': False},
    EventCode.ExitErrorAlarm: {
        'description': "Exit error alarm (zone)",
        'is_user': False},
    EventCode.PanicZoneTrouble: {
        'description': "Panic zone trouble",
        'is_user': False},
    EventCode.HoldUpZoneTrouble: {
        'description': "Hold-up zone trouble",
        'is_user': False},
    EventCode.SwingerTrouble: {
        'description': "Swinger Trouble",
        'is_user': False},
    EventCode.CrossZoneTrouble: {
        'description': "Cross-zone Trouble",
        'is_user': False},

    # Sensor Trouble -380
    EventCode.SensorTrouble: {
        'description': "Sensor trouble",
        'is_user': False},
    EventCode.LossOfSupervision_RF: {
        'description': "Loss of supervision - RF",
        'is_user': False},
    EventCode.LossOfSupervision_RPM: {
        'description': "Loss of supervision - RPM",
        'is_user': False},
    EventCode.SensorTamper_Trouble: {
        'description': "Sensor tamper",
        'is_user': False},
    EventCode.RFLowBattery: {
        'description': "RF low battery",
        'is_user': False},
    EventCode.SmokeDetectorHiSensitivity: {
        'description': "Smoke detector Hi sensitivity",
        'is_user': False},
    EventCode.SmokeDetectorLowSensitivity: {
        'description': "Smoke detector Low sensitivity",
        'is_user': False},
    EventCode.IntrusionDetectorHiSensitivity: {
        'description': "Intrusion detector Hi sensitivity",
        'is_user': False},
    EventCode.IntrusionDetectorLowSensitivity: {
        'description': "Intrusion detector Low sensitivity",
        'is_user': False},
    EventCode.SensorSelfTestFailure: {
        'description': "Sensor self-test failure",
        'is_user': False},
    EventCode.SensorWatchTrouble: {
        'description': "Sensor Watch trouble",
        'is_user': False},
    EventCode.DriftCompensationError: {
        'description': "Drift Compensation Error",
        'is_user': False},
    EventCode.MaintenanceAlert: {
        'description': "Maintenance Alert",
        'is_user': False},

    # OPEN/CLOSE/REMOTE ACCESS

    # Open/Close -400, 440,450
    EventCode.OpenClose: {
        'description': "Open/Close",
        'is_user': True},
    EventCode.OCByUser: {
        'description': "O/C by user",
        'is_user': True},
    EventCode.GroupOC: {
        'description': "Group O/C",
        'is_user': True},
    EventCode.AutomaticOC: {
        'description': "Automatic O/C",
        'is_user': True},
    EventCode.LateToOC: {
        'description': "Late to O/C  (Note: use 453, 454 instead )",
        'is_user': True},
    EventCode.DeferredOC: {
        'description': "Deferred O/C (Obsolete- do not use )",
        'is_user': True},
    EventCode.Cancel: {
        'description': "Cancel",
        'is_user': True},
    EventCode.RemoteArmDisarm: {
        'description': "Remote arm/disarm",
        'is_user': True},
    EventCode.QuickArm: {
        'description': "Quick arm",
        'is_user': True},
    EventCode.KeyswitchOC: {
        'description': "Keyswitch O/C",
        'is_user': True},
    EventCode.ArmedSTAY: {
        'description': "Armed STAY",
        'is_user': True},
    EventCode.KeyswitchArmedSTAY: {
        'description': "Keyswitch Armed STAY",
        'is_user': True},
    EventCode.ExceptionOC: {
        'description': "Exception O/C",
        'is_user': True},
    EventCode.EarlyOC: {
        'description': "Early O/C",
        'is_user': True},
    EventCode.LateOC: {
        'description': "Late O/C",
        'is_user': True},
    EventCode.FailedToOpen: {
        'description': "Failed to Open",
        'is_user': True},
    EventCode.FailedToClose: {
        'description': "Failed to Close",
        'is_user': True},
    EventCode.AutoArmFailed: {
        'description': "Auto-arm Failed",
        'is_user': True},
    EventCode.PartialArm: {
        'description': "Partial Arm",
        'is_user': True},
    EventCode.ExitError: {
        'description': "Exit Error (user)",
        'is_user': True},
    EventCode.UserOnPremises: {
        'description': "User on Premises",
        'is_user': True},
    EventCode.RecentClose: {
        'description': "Recent Close",
        'is_user': True},
    EventCode.WrongCodeEntry: {
        'description': "Wrong Code Entry",
        'is_user': False},
    EventCode.LegalCodeEntry: {
        'description': "Legal Code Entry",
        'is_user': True},
    EventCode.ReArmAfterAlarm: {
        'description': "Re-arm after Alarm",
        'is_user': True},
    EventCode.AutoArmTimeExtended: {
        'description': "Auto-arm Time Extended",
        'is_user': True},
    EventCode.PanicAlarmReset: {
        'description': "Panic Alarm Reset",
        'is_user': False},
    EventCode.ServiceOnOffPremises: {
        'description': "Service On/Off Premises",
        'is_user': True},

    # Remote Access -410
    EventCode.CallbackRequestMade: {
        'description': "Callback request made",
        'is_user': True},
    EventCode.SuccessfulDownloadAccess: {
        'description': "Successful download/access",
        'is_user': True},
    EventCode.UnsuccessfulAccess: {
        'description': "Unsuccessful access",
        'is_user': True},
    EventCode.SystemShutdownCommandReceived: {
        'description': "System shutdown command received",
        'is_user': True},
    EventCode.DialerShutdownCommandReceived: {
        'description': "Dialer shutdown command received",
        'is_user': True},
    EventCode.SuccessfulUpload: {
        'description': "Successful Upload",
        'is_user': False},

    # Access control -420,430
    EventCode.AccessDenied: {
        'description': "Access denied",
        'is_user': True},
    EventCode.AccessReportByUser: {
        'description': "Access report by user",
        'is_user': True},
    EventCode.ForcedAccess: {
        'description': "Forced Access",
        'is_user': False},
    EventCode.EgressDenied: {
        'description': "Egress Denied",
        'is_user': True},
    EventCode.EgressGranted: {
        'description': "Egress Granted",
        'is_user': True},
    EventCode.AccessDoorProppedOpen: {
        'description': "Access Door propped open",
        'is_user': False},
    EventCode.AccessPointDoorStatusMonitorTrouble: {
        'description': "Access point Door Status Monitor trouble",
        'is_user': False},
    EventCode.AccessPointRequestToExitTrouble: {
        'description': "Access point Request To Exit trouble",
        'is_user': False},
    EventCode.AccessProgramModeEntry: {
        'description': "Access program mode entry",
        'is_user': True},
    EventCode.AccessProgramModeExit: {
        'description': "Access program mode exit",
        'is_user': True},
    EventCode.AccessThreatLevelChange: {
        'description': "Access threat level change",
        'is_user': True},
    EventCode.AccessRelayTriggerFail: {
        'description': "Access relay/trigger fail",
        'is_user': False},
    EventCode.AccessRTEShunt: {
        'description': "Access RTE shunt",
        'is_user': False},
    EventCode.AccessDSMShunt: {
        'description': "Access DSM shunt",
        'is_user': False},

    # BYPASSES / DISABLES

    # System Disables -500 and 510
    EventCode.AccessReaderDisable: {
        'description': "Access reader disable",
        'is_user': False},

    # Sounder / Relay Disables -520
    EventCode.SounderRelayDisable: {
        'description': "Sounder/Relay Disable",
        'is_user': False},
    EventCode.Bell1Disable: {
        'description': "Bell 1 disable",
        'is_user': False},
    EventCode.Bell2Disable: {
        'description': "Bell 2 disable",
        'is_user': False},
    EventCode.AlarmRelayDisable: {
        'description': "Alarm relay disable",
        'is_user': False},
    EventCode.TroubleRelayDisable: {
        'description': "Trouble relay disable",
        'is_user': False},
    EventCode.ReversingRelayDisable: {
        'description': "Reversing relay disable",
        'is_user': False},
    EventCode.NotificationApplianceCkt3Disable: {
        'description': "Notification Appliance Ckt. # 3 disable",
        'is_user': False},
    EventCode.NotificationApplianceCkt4Disable: {
        'description': "Notification Appliance Ckt. # 4 disable",
        'is_user': False},

    # System Peripheral Disables -530 and 540
    EventCode.ModuleAdded: {
        'description': "Module Added",
        'is_user': False},
    EventCode.ModuleRemoved: {
        'description': "Module Removed",
        'is_user': False},

    # Communication Disables -550 and 560
    EventCode.DialerDisabled: {
        'description': "Dialer disabled",
        'is_user': False},
    EventCode.RadioTransmitterDisabled: {
        'description': "Radio transmitter disabled",
        'is_user': False},
    EventCode.RemoteUploadDownloadDisabled: {
        'description': "Remote Upload/Download disabled",
        'is_user': False},

    # Bypasses -570
    EventCode.ZoneSensorBypass: {
        'description': "Zone/Sensor bypass",
        'is_user': False},
    EventCode.FireBypass: {
        'description': "Fire bypass",
        'is_user': False},
    EventCode.AlwaysOnZoneBypass: {
        'description': "24 Hour zone bypass",
        'is_user': False},
    EventCode.BurgBypass: {
        'description': "Burg. Bypass",
        'is_user': False},
    EventCode.GroupBypass: {
        'description': "Group bypass",
        'is_user': True},
    EventCode.SwingerBypass: {
        'description': "Swinger bypass",
        'is_user': False},
    EventCode.AccessZoneShunt: {
        'description': "Access zone shunt",
        'is_user': False},
    EventCode.AccessPointBypass: {
        'description': "Access point bypass",
        'is_user': False},

    # TEST / MISC.

    # Test/Misc. -600, 610
    EventCode.ManualTriggerTestReport: {
        'description': "Manual trigger test report",
        'is_user': False},
    EventCode.PeriodicTestReport: {
        'description': "Periodic test report",
        'is_user': False},
    EventCode.PeriodicRFTransmission: {
        'description': "Periodic RF transmission",
        'is_user': False},
    EventCode.FireTest: {
        'description': "Fire test",
        'is_user': True},
    EventCode.StatusReportToFollow: {
        'description': "Status report to follow",
        'is_user': False},
    EventCode.ListenInToFollow: {
        'description': "Listen-in to follow",
        'is_user': False},
    EventCode.WalkTestMode: {
        'description': "Walk test mode",
        'is_user': True},
    EventCode.PeriodicTest_SystemTroublePresent: {
        'description': "Periodic test - System Trouble Present",
        'is_user': False},
    EventCode.VideoXmitterActive: {
        'description': "Video Xmitter active",
        'is_user': False},
    EventCode.PointTestedOK: {
        'description': "Point tested OK",
        'is_user': False},
    EventCode.PointNotTested: {
        'description': "Point not tested",
        'is_user': False},
    EventCode.IntrusionZoneWalkTested: {
        'description': "Intrusion Zone Walk Tested",
        'is_user': False},
    EventCode.FireZoneWalkTested: {
        'description': "Fire Zone Walk Tested",
        'is_user': False},
    EventCode.PanicZoneWalkTested: {
        'description': "Panic Zone Walk Tested",
        'is_user': False},
    EventCode.ServiceRequest: {
        'description': "Service Request",
        'is_user': False},

    # Event Log -620
    EventCode.EventLogReset: {
        'description': "Event Log reset",
        'is_user': False},
    EventCode.EventLog50PctFull: {
        'description': "Event Log 50% full",
        'is_user': False},
    EventCode.EventLog90PctFull: {
        'description': "Event Log 90% full",
        'is_user': False},
    EventCode.EventLogOverflow: {
        'description': "Event Log overflow",
        'is_user': False},
    EventCode.TimeDateReset: {
        'description': "Time/Date reset",
        'is_user': True},
    EventCode.TimeDateInaccurate: {
        'description': "Time/Date inaccurate",
        'is_user': False},
    EventCode.ProgramModeEntry: {
        'description': "Program mode entry",
        'is_user': False},
    EventCode.ProgramModeExit: {
        'description': "Program mode exit",
        'is_user': False},
    EventCode.Hour32EventLogMarker: {
        'description': "32 Hour Event log marker",
        'is_user': False},

    # Scheduling -630
    EventCode.ScheduleChange: {
        'description': "Schedule change",
        'is_user': False},
    EventCode.ExceptionScheduleChange: {
        'description': "Exception schedule change",
        'is_user': False},
    EventCode.AccessScheduleChange: {
        'description': "Access schedule change",
        'is_user': False},

    # Personnel Monitoring -640
    EventCode.SeniorWatchTrouble: {
        'description': "Senior Watch Trouble",
        'is_user': False},
    EventCode.LatchKeySupervision: {
        'description': "Latch-key Supervision",
        'is_user': True},

    # Misc. -650
    EventCode.ReservedForAdemcoUse: {
        'description': "Reserved for Ademco Use",
        'is_user': False},
    EventCode.ReservedForAdemcoUse2: {
        'description': "Reserved for Ademco Use",
        'is_user': True},
    EventCode.ReservedForAdemcoUse3: {
        'description': "Reserved for Ademco Use",
        'is_user': True},
    EventCode.SystemInactivity: {
        'description': "System Inactivity",
        'is_user': False},
}
