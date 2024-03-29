# LifeSOSpy

***Note: This project is no longer being developed.***

[![PyPI version](https://badge.fury.io/py/lifesospy.svg)](https://badge.fury.io/py/lifesospy)

A Python library to communicate with [LifeSOS](http://lifesos.com.tw)
alarm systems. In some markets, they may also be labelled under the name
of the distributor; eg. SecurePro in Australia, WeBeHome in northern
Europe.

It was written for & tested with the LS-30 model, though it should also
work on the LS-10/LS-20 models.

The base unit must be connected to your network in order for this
library to communicate with it; serial connections are not currently
supported.

Note: This library is intended for developer use. If you're just
looking to access your LifeSOS alarm system, devices and switches from
other applications, I'd suggest taking a look at
[LifeSOSpy_MQTT](https://github.com/rorr73/LifeSOSpy_MQTT) instead.
It provides an MQTT Client implementation that easily integrates with
applications that support MQTT (eg. Home Assistant, OpenHAB).

---

When using this library in your app there are three main classes to
choose from:

### BaseUnit

Provides higher level access to the alarm system, managing the Client
/ Server connection for you. It will automatically enumerate all
attached devices on connection, monitor the state of the base unit
& devices with notification when they change, and automatically
attempt reconnection (when running as client).

This class was created to simplify integration into home automation
software.

### Client / Server

These two classes allow you to directly issue commands to the alarm
system, and attach callbacks to handle any events if needed.

##### Simple Client Examples

###### Display the current mode

```python
from lifesospy.client import Client
from lifesospy.command import GetOpModeCommand

client = Client('192.168.1.100', 1680)
await client.async_open()
response = await client.async_execute(GetOpModeCommand())
print("Operation mode is {}".format(str(response.operation_mode)))
client.close()
```
> Operation mode is Disarm

###### Arm the system

```python
from lifesospy.client import Client
from lifesospy.command import SetOpModeCommand
from lifesospy.enums import OperationMode

client = Client('192.168.1.100', 1680)
await client.async_open()
await client.async_execute(SetOpModeCommand(OperationMode.Away))
client.close()
```
