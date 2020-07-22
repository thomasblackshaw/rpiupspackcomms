#!/usr/bin/python3

'''
example --- Python script to use the RPi UPSPack Standard V2's monitor script

Equipment needed:=
- UPS board --- www.makersmthing.com/...
- USB-to-TTL converter --- www.friendlyarm.com/
'''

import copy
import datetime
import os
import random
from threading import Condition, Lock, Thread
from time import sleep

try:
    import serial
except ImportError as ex:
    raise ImportError("Please install pySerial module (Python 3)")
import time

from smartupscontroller import SmartUPS


def __main__():
    print("serial device = %s" % read_smartups_output(SmartUPS.serial_device))
    SmartUPS.verbose
    SmartUPS.batterylevel
    SmartUPS.discharging
    SmartUPS.charging
    SmartUPS.Vout
    from time import sleep
    while True:
        print("Vout=%1.4f; charging?%s; discharging?%s; batterylevel=%d%%; timeleft=%s; verbose=%s" % (SmartUPS.Vout, 'Yes' if SmartUPS.charging else 'No',
                            'Yes' if SmartUPS.discharging else 'No', SmartUPS.batterylevel, ((str(SmartUPS.timeleft // 60) + 'm') if SmartUPS.timeleft is not None else '?'), SmartUPS.verbose))
        sleep(5)

