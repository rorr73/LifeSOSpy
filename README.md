# LifeSOSpy

A Python library to communicate with [LifeSOS](http://lifesos.com.tw)
alarm systems. In some markets, they may be labelled under the name of
the distributor; eg. SecurePro in Australia, WeBeHome in northern
Europe.

It was written for & tested with the LS-30 model, though it should also
work on the LS-10/LS-20 models.

The base unit must be connected to your network in order for this
library to communicate with it, and the network interface configured as
a **TCP Server**. This is the default setting when using the
HyperSecureLink software included with the alarm system, so if
you encounter any issues I would recommend referring to the manual and
setting that up first.

Please note that Serial connections are not currently supported.

When using this library in your app there are two main classes to
choose from:

##### Client

Allows you to directly issue commands to the alarm system, and attach
callbacks to handle any events if needed.

##### BaseUnit

Provides higher level access to the alarm system by managing the Client
connection for you. It will reconnect on failure, automatically
enumerate all attached devices, and monitors the state of the base unit
& devices with notification when they change.

This class was created to simplify integration into home automation
software.

## Examples

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
