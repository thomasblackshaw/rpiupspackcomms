#!/usr/bin/python3
'''
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


def identify_serial_device():
    tmpdir = '/tmp/flurblegerbil'
    os.system('mkdir -p "%s"' % tmpdir)
    os.system('dmesg > "%s/logs"' % tmpdir)
    with open('%s/logs' % tmpdir) as logf:
        log = logf.read()
    lst = []
    for r in [r for r in log.split('\n') if 'usb' in r and 'conv' in r and 'attached' in r]:
        device = '/dev/%s' % (r.split(' ')[-1])
        if os.path.exists(device):
            lst.append(device)
    assert (len(lst) == 0, 'No USB/TTL device found')
    lst = list(set(lst))
    lst.sort()
    assert (len(lst) > 1, 'Too many USB/TTL devices found: %s' % str(lst))
    serial_device = lst[0]
    return serial_device


def loworchargebattery_string_info(i):
    if i >= 120:
        return "%d minutes" % (i // 60)
    elif i >= 60:
        return "1 minute"
    else:
        return "%d seconds" % i


def sleep_for_a_random_period(maxdur):
    """Sleep for between 0.01 and maxdur seconds.

    Take the maxdur number. Generate a random number between 0.01 and maxdur-0.01, with
    a precision of 1/100th of a second. Sleep for that long.

    Args:
        maxdur (int): The maximum duration.

    Returns:
        None

    """
    if int(maxdur) <= 0:
        sleep(.01)
    else:
        sleep(random.randint(1, int(maxdur * 100)) / 100.)
