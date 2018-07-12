LifeSOSpy
=========

A Python library to communicate with `LifeSOS`_ alarm systems. In some
markets, they may be labelled under the name of the distributor; eg.
SecurePro in Australia, WeBeHome in northern Europe.

It was written for & tested with the LS-30 model, though it should also
work on the LS-10/LS-20 models.

The base unit must be connected to your network in order for this
library to communicate with it; serial connections are not currently
supported.

When using this library in your app there are three main classes to
choose from:

Client / Server
'''''''''''''''

These two classes allow you to directly issue commands to the alarm
system, and attach callbacks to handle any events if needed.

BaseUnit
''''''''

Provides higher level access to the alarm system, managing the Client /
Server connection for you. It will automatically enumerate all attached
devices on connection, monitor the state of the base unit & devices with
notification when they change, and automatically attempt reconnection
(when running as client).

This class was created to simplify integration into home automation
software.

Simple Client Examples
----------------------

Display the current mode


.. code:: python

   from lifesospy.client import Client
   from lifesospy.command import GetOpModeCommand

   client = Client('192.168.1.100', 1680)
   await client.async_open()
   response = await client.async_execute(GetOpModeCommand())
   print("Operation mode is {}".format(str(response.operation_mode)))
   client.close()

..

   Operation mode is Disarm

Arm the system


.. code:: python

   from lifesospy.client import Client
   from lifesospy.command import SetOpModeCommand
   from lifesospy.enums import OperationMode

   client = Client('192.168.1.100', 1680)
   await client.async_open()
   await client.async_execute(SetOpModeCommand(OperationMode.Away))
   client.close()

.. _LifeSOS: http://lifesos.com.tw