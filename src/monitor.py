#!/usr/bin/python3

'''
main --- Python script to use the RPi UPSPack Standard V2's monitor script

Equipment needed:=
- UPS board --- www.makersmthing.com/...
- USB-to-TTL converter --- www.friendlyarm.com/


#     SmartUPS.verbose
#     SmartUPS.batterylevel
#     SmartUPS.discharging
#     SmartUPS.charging
#     SmartUPS.Vout


'''

import os


# try:
#     import serial
# except ImportError as ex:
#     raise ImportError("Please install pySerial module (Python 3)")
def send_global_message(msg):
    msg = msg.replace(';', '.').replace("'", '')
    os.system("wall '%s'" % msg)
    os.system('''
msg="%s"
for u in $(users); do
    for disp in 0 1 2 3 ; do
        su -l $u -c "DISPLAY=:$disp xmessage -timeout 10 '$msg'" 2> /dev/null &
    done
done
''' % msg)


if __name__ == "__main__":
    from pyupspack import SmartUPS
    from time import sleep
    loops_since_last_warning = 999999
    while True:
        if SmartUPS.Vout is None:
            s = "Waiting for UPS to connect"
        else:
            s = "Vout=%1.4f; charging?%s; discharging?%s; batterylevel=%d%%; timeleft=%s; verbose=%s" % (SmartUPS.Vout, 'Yes' if SmartUPS.charging else 'No',
                        'Yes' if SmartUPS.discharging else 'No', SmartUPS.batterylevel, ('?' if SmartUPS.timeleft is None else (str(SmartUPS.timeleft // 60) + 'm')), SmartUPS.verbose)
        print(s)
        with open("/var/log/rpiupspackcomms", "a") as f:
            f.write(s + '\n')
        if SmartUPS.charging:
            if loops_since_last_warning > 0:
                loops_since_last_warning = 0
                send_global_message(SmartUPS.verbose)  # """Power is back online.""")
        if SmartUPS.discharging and SmartUPS.batterylevel is not None and SmartUPS.batterylevel < 10:
            loops_since_last_warning += 1
            if loops_since_last_warning > SmartUPS.batterylevel:  # 11:
                loops_since_last_warning = 0
                send_global_message(SmartUPS.verbose)
#                 """Power is offline.
# Battery level is at %d%% and falling.
# %d minutes remaining""" % (SmartUPS.batterylevel, SmartUPS.timeleft // 60))
        if SmartUPS.batterylevel is not None and SmartUPS.batterylevel < 10:
            send_global_message("SHUTTING DOWN")
            os.system("shutdown -h now")
        sleep(5)

