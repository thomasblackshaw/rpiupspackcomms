#!/usr/bin/python3

'''
example --- Python script to use the RPi UPSPack Standard V2's monitor script

Equipment needed:=
- UPS board --- www.makersmthing.com/...
- USB-to-TTL converter --- www.friendlyarm.com/
'''

# try:
#     import serial
# except ImportError as ex:
#     raise ImportError("Please install pySerial module (Python 3)")


def __main__():
    from pyupspack import SmartUPS
#     print("serial device = %s" % SmartUPS._forgivingly_read_smartups_output())
#     SmartUPS.verbose
#     SmartUPS.batterylevel
#     SmartUPS.discharging
#     SmartUPS.charging
#     SmartUPS.Vout
    from time import sleep
    while True:
        print("Vout=%1.4f; charging?%s; discharging?%s; batterylevel=%d%%; timeleft=%s; verbose=%s" % (SmartUPS.Vout, 'Yes' if SmartUPS.charging else 'No',
                            'Yes' if SmartUPS.discharging else 'No', SmartUPS.batterylevel, ((str(SmartUPS.timeleft // 60) + 'm') if SmartUPS.timeleft is not None else '?'), SmartUPS.verbose))
        sleep(5)

