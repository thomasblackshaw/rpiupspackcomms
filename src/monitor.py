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
    * You have to also use ``sphinx.ext.todo`` extension

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

"""
import os


# try:
#     import serial
# except ImportError as ex:
#     raise ImportError("Please install pySerial module (Python 3)")
def send_global_message(msg):
    """Send message to all console users and all XWindow users.
    
    By calling 'wall' and 'xmessage', send the specified message to all users.
    I do my best to filter out weird characters that may be present in 'msg'.

    Args:
        msg (str): The message to be sent.

    Returns:
        None.

    .. _PEP 484:
        https://www.python.org/dev/peps/pep-0484/

    """
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
            if loops_since_last_warning > SmartUPS.batterylevel:
                loops_since_last_warning = 0
                send_global_message(SmartUPS.verbose)
        if SmartUPS.batterylevel is not None and SmartUPS.batterylevel < 10:
            send_global_message("SHUTTING DOWN")
            os.system("shutdown -h now")
        sleep(5)
