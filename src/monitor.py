#!/usr/bin/python3

"""Monitor output of RPi UPSPack. Warn user if power low. Shutdown if necessary.

This program monitors the output of the RPi UPSPack circuit board. When the
battery begins discharging or begins charging, the users are warned via console
walls and by calls to xmessage. If discharging continues, warnings continue to
occur with greater frequency, until a shutdown occurs (if the battery level dips
too low).

Example:
    Here is how to run me::

        $ python3 monitor.py

I do not terminate unless you tell me to terminate. I'm tough like that.

Attributes:
    None

Todo:
    * For module TODOs
    * QQQ

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

"""
import os
from pyupspack.utilities import send_global_message

# try:
#     import serial
# except ImportError as ex:
#     raise ImportError("Please install pySerial module (Python 3)")


def generate_our_logging_string():
    if SmartUPS.Vout is None:
        return "Waiting for UPS to connect"
    else:
        return "Vout=%1.4f; charging?%s; discharging?%s; batterylevel=%d%%; timeleft=%s; verbose=%s" % (SmartUPS.Vout, 'Yes' if SmartUPS.charging else 'No',
                    'Yes' if SmartUPS.discharging else 'No', SmartUPS.batterylevel, ('?' if SmartUPS.timeleft is None else (str(SmartUPS.timeleft // 60) + 'm')), SmartUPS.verbose)


def generate_echo_and_log_our_logging_string():
    loggingstring = generate_our_logging_string()
    print(loggingstring)
    with open("/var/log/rpiupspackcomms", "a") as f:
        f.write(loggingstring + '\n')


if __name__ == "__main__":
    """Monitor UPSPack. Provide meaningful logging. Warn user if battery is low. Shut down gracefully if too low.
    
    Using the pyupspack.SmartUPS (Python 3) library, monitor the telemetry coming in from the UPSPack battery
    pack/charger/UPS. If the status changes -- for example, if the device switches from battery to mains or
    vice versa -- notify the user. If the battery level dips below a certain level, notify the user. If the
    battery level dips below 10%, shut down the computer gracefully.
    """
    from pyupspack import SmartUPS
    from time import sleep
    loops_since_last_warning = 999999
    while True:
        generate_echo_and_log_our_logging_string()
        if SmartUPS.charging:
            # Tell all users *once*, the power is back online.
            if loops_since_last_warning > 0:
                loops_since_last_warning = 0
                send_global_message(SmartUPS.verbose)
        if SmartUPS.discharging and SmartUPS.batterylevel is not None and SmartUPS.batterylevel >= 10:
            # Tell all users repeatedly (with a decent pause in between), we're running on batteries
            loops_since_last_warning += 1
            if loops_since_last_warning > SmartUPS.batterylevel:
                loops_since_last_warning = 0
                send_global_message(SmartUPS.verbose)
        if SmartUPS.batterylevel is not None and SmartUPS.batterylevel < 10:
            send_global_message("SHUTTING DOWN")
            os.system("shutdown -h now")
        sleep(5)
