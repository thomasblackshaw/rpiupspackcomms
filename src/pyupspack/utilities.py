#!/usr/bin/python3
"""Example Google style docstrings.

This module demonstrates documentation as specified by the `Google Python
Style Guide`_. Docstrings may extend over multiple lines. Sections are created
with a section header and a colon followed by a block of indented text.

Example:
    Examples can be given using either the ``Example`` or ``Examples``
    sections. Sections support any reStructuredText formatting, including
    literal blocks::

        $ python example_google.py

Section breaks are created by resuming unindented text. Section breaks
are also implicitly created anytime a new section starts.

Attributes:
    module_level_variable1 (int): Module level variables may be documented in
        either the ``Attributes`` section of the module docstring, or in an
        inline docstring immediately following the variable.

        Either form is acceptable, but the two should not be mixed. Choose
        one convention to document module level variables and be consistent
        with it.

Todo:
    * For module TODOs
    * QQQ

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

"""
import os
import random
from time import sleep
from pyupspack.exceptions import SmartUPSInitializationError


def identify_serial_device():
    """Find the serial device associated with the UPSPack circuit board.
    
    By examining the output of 'dmesg', locate the serial/USB device associated
    with the RPi UPSPack circuit board. The returned value should be
    /dev/{something}

    Note:
        This probably won't work on FreeBSD, MacOS, or any other OS (but Linux).

    Args:
        None

    Returns:
        bool: The return value. True for success, False otherwise.
    
    Raises:
        SmartUPSInitializationError: Cannot find the device.

    .. _PEP 484:
        https://www.python.org/dev/peps/pep-0484/

    """
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
    lst = list(set(lst))
    lst.sort()
    if len(lst) > 1:
        raise SmartUPSInitializationError("I found %d USB/TTL devices. Please specify the one I should use." % len(lst))
    if len(lst) == 0:
        raise SmartUPSInitializationError("I found zero USB/TTL devices. Please install or find one.")
    serial_device = lst[0]
    return serial_device


def loworchargebattery_string_info(i):
    """Turn an integer into a number of seconds or minutes.

    Take the specified integer. If below 60, return "N//60 seconds".
    If 60-119, return "1 minute". If >=120, return "N//60 minutes".
    You get the idea. 

    Args:
        param1 (int): The number of seconds.

    Returns:
        str: The human-readable version, in seconds or minutes.

    .. _PEP 484:
        https://www.python.org/dev/peps/pep-0484/

    """
    if i >= 120:
        return "%d minutes" % (i // 60)
    elif i >= 60:
        return "1 minute"
    elif i == 1:
        return "1 second"
    elif type(i) is int:
        return "%d seconds" % i
    elif type(i) is float:
        return "%f seconds" % i
    else:
        return "%s seconds" % i


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
