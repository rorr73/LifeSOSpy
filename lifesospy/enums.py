import sys

from enum import IntEnum
if float('%s.%s' % sys.version_info[:2]) >= 3.6:
    from enum import IntFlag
else:
    from aenum import IntFlag

class DeviceType(IntEnum):
    """Indicates the type of LifeSOS device."""
    HumidSensor = 0x01
    HumidSensor2 = 0x02
    TempSensor = 0x03
    TempSensor2 = 0x04
    FloodDetector = 0x05
    FloodDetector2 = 0x06
    MedicalButton = 0x08
    LightSensor = 0x0a
    LightDetector = 0x0b
    InactivityReport = 0x0c
    AnalogSensor = 0x0e
    AnalogSensor2 = 0x0f
    RemoteController = 0x10
    CardReader = 0x12
    KeyPad = 0x18
    XKeyPad = 0x19
    SmokeDetector = 0x20
    PressureSensor = 0x22
    PressureSensor2 = 0x23
    CODetector = 0x25
    CO2Sensor = 0x26
    CO2Sensor2 = 0x27
    ACCurrentMeter = 0x28
    ACCurrentMeter2 = 0x29
    ThreePhaseACMeter = 0x2b
    GasDetector = 0x30
    DoorMagnet = 0x40
    Repeater = 0x41
    VibrationSensor = 0x42
    PIRSensor = 0x50
    StatusIndicator = 0x56
    Repeater2 = 0x57
    GlassBreakDetector = 0x60
    RemoteSiren = 0x70
    BaseUnit = 0x80
    RFBell = 0x90
    RFSW = 0xA0
    RWSWOnTime = 0xA1
    RFSiren = 0xC0
    RFSirenOnTime = 0xC1

    @classmethod
    def has_value(cls, value):
        return any(value == item.value for item in cls)

class EventCode(IntEnum):
    """Type of event raised by a device."""
    Test = 0x0a01
    Away = 0x0a10
    Disarm = 0x0a14
    Home = 0x0a18
    Heartbeat = 0x0a20
    NewBattery = 0x0a2a
    LowBattery = 0x0a30
    Open = 0x0a40
    Close = 0x0a48
    Tamper = 0x0a50
    Trigger = 0x0a58
    Panic = 0x0a60

    @classmethod
    def has_value(cls, value):
        return any(value == item.value for item in cls)

class OperationMode(IntEnum):
    """Mode of operation for the base unit."""
    Disarm = 0x0
    Home = 0x1
    Away = 0x2
    Monitor = 0x8

    @classmethod
    def has_value(cls, value):
        return any(value == item.value for item in cls)

class DCFlags(IntFlag):
    """Device Characteristics flags."""
    Repeater = 0x80
    BaseUnit = 0x40
    TwoWay = 0x20
    Supervisory = 0x10
    RFVoice = 0x08
    Reserved_b2 = 0x04
    Reserved_b1 = 0x02
    Reserved_b0 = 0x01

class ESFlags(IntFlag):
    """Enable Status flags."""
    Bypass = 0x8000
    Delay = 0x4000
    Hour24 = 0x2000
    HomeGuard = 0x1000
    WarningBeepDelay = 0x0800
    PreWarning = 0x0800
    AlarmSiren = 0x0400
    Bell = 0x0200
    Latchkey = 0x0100
    Inactivity = 0x0100
    Reserved_b7 = 0x0080
    Reserved_b6 = 0x0040
    TwoWay = 0x0020
    Supervised = 0x0010
    RFVoice = 0x0008
    HomeAuto = 0x0004
    Reserved_b1 = 0x0002
    Reserved_b0 = 0x0001

class SSFlags(IntFlag):
    """Special Sensor Status flags."""
    ControlAlarm = 0x80
    HighLowOperation = 0x40
    HighTriggered = 0x20
    LowTriggered = 0x10
    HighState = 0x08
    LowState = 0x04
    Reserved_b1 = 0x02
    Reserved_b0 = 0x01
