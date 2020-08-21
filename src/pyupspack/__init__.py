#!/usr/bin/python3
"""Python library to monitor the RPi UPSPack Standard V2.

The module 'pyupspack' facilitates communication between the RPi UPSPack Standard
V2 and a GNU/Linux-based OS that possesses a decent Python 3 implementation. The
library is utilized by the monitor.py executable. The communication consists of
reading the human-readable output from the detected TTL-USB interface and processing
it into something meaningful. The RPi UPSPack may be purchased from
```https://www.makerfocus.com/products/raspberry-pi-expansion-board-ups-pack-standard-power-supply```.

Example:
    Here is a simple example of how to use the library:
    
    $ python3
    >>> from pyupspack import SmartUPS
    >>> import time
    >>> while True:
    >>>     print(SmartUPS.verbose)
    >>>     if SmartUPS.batterylevel is not None and SmartUPS.batterylevel < 10:
    >>>         os.system("shutdown -h now")
    >>>     time.sleep(5)
    >>>

Note:
    For a full list of attributes and methods, see the SmartUPSInterface source code.

Todo: QQQ
    * For module TODOs
    * QQQ

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

"""

import copy
import datetime
import os
import random
from threading import Condition, Lock, Thread
from time import sleep
import time

from pyupspack.classes import ReadWriteLock, DummyCachingCall, SelfCachingCall
from pyupspack.exceptions import ReadSmartUPSError, ReadOnlyError, CachingStructureInitializationError, CachingStructurePrematureReadError
from pyupspack.utilities import identify_serial_device, loworchargebattery_string_info, sleep_for_a_random_period

try:
    import serial
except ImportError as ex:
    raise ImportError("Please install pySerial module (Python 3)")


class SmartUPSInterface:
    """Interface class for the RPi UPSPack Standard V2
    
    This library facilitates communication between the RPi UPSPack Standard V2 and a
    single-board computer of your choosing. Connect the UPSPack to a USB port on your
    computer and interface with it.

    Attributes:
        Vout (float): Voltage out from the UPSPack's battery.
            If unknown, returns None.
    
        batterylevel (int): Between 0 and 100, with 100==full and 0=empty.
            If unknown, returns None.
        
        timeleft (int): Time until battery empties/fills entirely.
            If unknown, returns None.
    
        cached_smartups (str): The cached version of _latest_serial_rx. Please use
            this, rather than _latest_serial_rx, because it is cached and therefore
            doesn't cause you to wait for the serial port to spit something out.
    
        charging (bool): If the UPSPack is charging, True; else, False.
            If unknown, returns None.
    
        discharging (bool): If the UPSPack is discharging, True; else, False.
            If unknown, returns None.
        
        hardwareversion (str): The current hardware version of the UPSPack.

        _latest_serial_rx (str): The latest human-readable output from the detected
            USB port. This is drawn from the port immediately.
            
        serial_device (str): The serial device with which we're communicating. This
            was set by SmartUPS when the instance was created.
        
        timeleft (int): The amount of time left before battery is full/empty.
            If unknown, returns None.
            
        verbose (str): The verbose, made-by-me, human-readable output that describes
            the current status of the UPSPack.
                
    Methods:
        _return_meaningful_status (): Returns dictionary of attributes derived
            from the cached output of the SmartUPSInterface's serial device.

        module_level_variable1 (int): Module level variables may be documented in
            either the ``Attributes`` section of the module docstring, or in an
            inline docstring immediately following the variable.
            
        Todo:
        * For module TODOs
        * QQQ
    
    .. _Google Python Style Guide:
       http://google.github.io/styleguide/pyguide.html

    """

    def __init__(self, serial_device, use_caching=True, baudrate=9600, pause_duration_between_uncached_reads=5):
        """The __init__ method of the SmartUPSInterface class.

        Note:
            The only instance that should be created (or used) is the SmartUPS instance.

        Args:
            serial_device (str): Serial device that the RPi UPSPack is using.
            use_caching (bool): If True, use an internally cached copy of the output of the
                serial device. Otherwise, read a fresh copy whenever it's needed.
            pause_duration_between_uncached_reads (:obj:`int`, optional): How often should the cache
                be updated? This must be a nonzero positive integer.

        Methods:
            ...lots of protected methods; no public ones.

        Raises:
            ValueError: Bad parameters were supplied by the programmer.
            InitializationError: I failed to initialize this class instance.

        """
        self.__serialdev_lck = ReadWriteLock()
        self.__smupsinfo_lck = ReadWriteLock()
        self.__battlevel_lck = ReadWriteLock()
        self.__smversion_lck = ReadWriteLock()
        self.__verbostxt_lck = ReadWriteLock()
        self.__time_left_lck = ReadWriteLock()
        self.__Volts_out_lck = ReadWriteLock()
        self.__dischargg_lck = ReadWriteLock()
        self.__charging_lock = ReadWriteLock()
        self.__serial_rx_lck = ReadWriteLock()
        self.__serial_device = serial_device
        self._last_time_we_read_smartups = None
        self._last_smartups_output = None
        self._our_timeremainingestimate_dct = {}  # Used by timeleft_and_verboseinfo()
        self._when_did_we_start_discharging = None
        self._when_did_we_start_recharging = None
        self._what_was_battery_level_when_we_did_start_disch_or_rchgg = None
        self._verbose_werewechargingordischarging = None
        self._serial_iface = serial.Serial(
            port=serial_device,
            baudrate=baudrate,
            timeout=1,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS
        )
        if serial_device is None or type(serial_device) is not str or not os.path.exists(serial_device):
            raise ValueError("serial_device should be a string and also an existent filename/device")
        if type(pause_duration_between_uncached_reads) is not int or pause_duration_between_uncached_reads < 1:
            raise ValueError("pause_duration_between_uncached_reads must be a nonzero positive integer")
#         os.system("stty -F %s 9600 cs8 -cstopb -parenb" % self.__serial_device)
        self.__cached_smartups = DummyCachingCall(pause_duration_between_uncached_reads, self._forgivingly_read_smartups_output) \
                                if not use_caching else \
                                SelfCachingCall(pause_duration_between_uncached_reads, self._forgivingly_read_smartups_output)  # , self.serial_device)
        self.__cached_smartups._update_me()
#        self._wait_until_nonNone_cached_result()
        super().__init__()

    def _forgivingly_read_smartups_output(self):
        """Up to ten times, try to obtain a dictionaryized output of the RPi UPSPack's USB port.
        
        Returns:
            dict: A simple dictionary of the output. The structure tends to look like this:-
                {'Vin':'...', 'Vout':'...', 'hardwareversion':'...', 'BATCAP':'...','SmartUPS':'...'} 
        
        Args:
            None

        Raises:
            ReadSmartUPSError: I failed to obtain any meaningful output.

        """
        for attempts in range(10):
            try:
                res = self._read_smartups_output()
                return res
            except Exception:
                sleep_for_a_random_period(.5)
        raise ReadSmartUPSError("Attempted %d times to read the smartUPS output. Failed totally." % attempts)

    def _wait_until_nonNone_cached_result(self):
        """Wait until the caching subroutine has actually interrogated the USB port and has stored a meaningful result.
        
        Returns:
            None
        
        Args:
            None

        Raises:
            ? QQQ
        
        """
        res = None
        attempts = 0
        while res is None:
            try:
                res = self.cached_smartups.result
            except Exception:
                sleep_for_a_random_period(1)
                attempts += 1
                if attempts > 100:
                    raise CachingStructureInitializationError("Failed to initialize the SmartUPS interface")

    @property
    def _latest_serial_rx(self):
        """Lockingly/synchronously read the latest string from our USB port. Return it.

        Returns:
            str: The one-line text, without '\n' on the end

        Args:
            None

        Raises:
            ? QQQ

        """
        try:
            self.__serial_rx_lck.acquire_read()
#             txt = ''
#             while txt.count('$') < 2:
#                 with open(serial_device, 'rt') as f:
#                     txt += f.readline().strip('\n')
#             txt = [r.strip(' ') for r in txt.strip(' \n ').split('$') if r != ''][-1]
            retval = ''
            while len(retval) == 0 or retval[-1] != '\n':
                retval = retval + self._serial_iface.read(999999).decode()
            return retval.strip('\n').split('\n')[-1]
        finally:
            self.__serial_rx_lck.release_read()
        return retval

    @_latest_serial_rx.setter
    def _latest_serial_rx(self, value):
        raise ReadOnlyError("Cannot set cached_smartups attribute. That is inappropriate!")

    def _read_smartups_output(self):  # FIXME: add a read-write lock for self._last_time_we_read_smartups etc.
        """Return either (a) our cached copy or (b) the output of _latest_serial_rx(), depending on the time elapsed.

        Returns:
            str: The one-line text, without '\n' on the end

        Args:
            None

        Raises:
            ? QQQ

        """
        current_timestamp = datetime.datetime.now()
        if self._last_time_we_read_smartups is None or (current_timestamp - self._last_time_we_read_smartups).seconds >= 1:
            self._last_time_we_read_smartups = current_timestamp
            self._last_smartups_output = self._latest_serial_rx
        txt = self._last_smartups_output
        if txt is None:
            return None
        incoming_info_lst = txt.strip('\n').strip(' ').strip('$').strip(' ').split(',')
        dct = {}
        for item in incoming_info_lst:
            p = item.find(' ')
            if p < 0:
                dct[p] = ''
            else:
                dct[item[:p]] = item[p + 1:]
        if dct['Vin'] == 'GOOD':
            if self._when_did_we_start_recharging is None:
                self._when_did_we_start_recharging = datetime.datetime.now()
                self._when_did_we_start_discharging = None
                self._what_was_battery_level_when_we_did_start_disch_or_rchgg = int(dct['BATCAP'])
                self._our_timeremainingestimate_dct = {}  # Used by timeleft_and_verboseinfo()
                if self._verbose_werewechargingordischarging is None:
                    self._verbose_werewechargingordischarging = 'charging'
        else:
            if self._when_did_we_start_discharging is None:
                self._when_did_we_start_discharging = datetime.datetime.now()
                self._when_did_we_start_recharging = None
                self._our_timeremainingestimate_dct = {}  # Used by timeleft_and_verboseinfo()
                self._what_was_battery_level_when_we_did_start_disch_or_rchgg = int(dct['BATCAP'])
                if self._verbose_werewechargingordischarging is None:
                    self._verbose_werewechargingordischarging = 'discharging'
        return dct

    @property
    def serial_device(self):
        try:
            self.__serialdev_lck.acquire_read()
            retval = self.__serial_device
        finally:
            self.__serialdev_lck.release_read()
        return retval

    @serial_device.setter
    def serial_device(self, value):
        raise ReadOnlyError("Cannot set serial_device attribute. That is inappropriate!")

    @property
    def cached_smartups(self):
        try:
            self.__smupsinfo_lck.acquire_read()
            retval = self.__cached_smartups
        finally:
            self.__smupsinfo_lck.release_read()
        return retval

    @cached_smartups.setter
    def cached_smartups(self, value):
        raise ReadOnlyError("Cannot set cached_smartups attribute. That is inappropriate!")

    @property
    def charging(self):
        try:
            self.__charging_lock.acquire_read()
            try:
                retval = True if self.__cached_smartups.result['Vin'] == 'GOOD' and self.__cached_smartups.result['BATCAP'] != '100' else False
            except (TypeError, AttributeError):
                return None
        finally:
            self.__charging_lock.release_read()
        return retval

    @charging.setter
    def charging(self, value):
        raise ReadOnlyError("Cannot set charging attribute. That is inappropriate!")

    @property
    def discharging(self):
        try:
            self.__dischargg_lck.acquire_read()
            try:
                retval = False if self.__cached_smartups.result['Vin'] == 'GOOD' else True
            except (TypeError, CachingStructurePrematureReadError):
                return None
        finally:
            self.__dischargg_lck.release_read()
        return retval

    @discharging.setter
    def discharging(self, value):
        raise ReadOnlyError("Cannot set discharging attribute. That is inappropriate!")

    @property
    def batterylevel(self):
        try:
            self.__battlevel_lck.acquire_read()
            try:
                retval = int(self.__cached_smartups.result['BATCAP'])
            except (TypeError, ValueError, CachingStructurePrematureReadError):
                retval = None
        finally:
            self.__battlevel_lck.release_read()
        return retval

    @batterylevel.setter
    def batterylevel(self, value):
        raise ReadOnlyError("Cannot set batterylevel attribute. That is inappropriate!")

    @property
    def Vout(self):
        try:
            self.__Volts_out_lck.acquire_read()
            try:
                retval = float(self.__cached_smartups.result['Vout']) / 1000.
            except (TypeError, ValueError, CachingStructurePrematureReadError):
                retval = None
        finally:
            self.__Volts_out_lck.release_read()
        return retval

    @Vout.setter
    def Vout(self, value):
        raise ReadOnlyError("Cannot set Vout attribute. That is inappropriate!")

    @property
    def hardwareversion(self):
        try:
            self.__smversion_lck.acquire_read()
            try:
                retval = self.__cached_smartups.result['SmartUPS']
            except (TypeError, ValueError, CachingStructurePrematureReadError):
                retval = None
        finally:
            self.__smversion_lck.release_read()
        return retval

    @hardwareversion.setter
    def hardwareversion(self, value):
        raise ReadOnlyError("Cannot set Vout attribute. That is inappropriate!")

    @property
    def verbose(self):
        try:
            self.__verbostxt_lck.acquire_read()
            try:
                retval = self.timeleft_and_verboseinfo()[1]
            except (TypeError, ValueError, CachingStructurePrematureReadError):
                return None
        finally:
            self.__verbostxt_lck.release_read()
        return retval

    @verbose.setter
    def verbose(self, value):
        raise ReadOnlyError("Cannot set Voutverboseattribute. That is inappropriate!")

    @property
    def timeleft(self):
        try:
            self.__time_left_lck.acquire_read()
            retval = self.timeleft_and_verboseinfo()[0]
        finally:
            self.__time_left_lck.release_read()
        return retval

    @timeleft.setter
    def timeleft(self, value):
        raise ReadOnlyError("Cannot set timeleft attribute. That is inappropriate!")

    def timeleft_and_verboseinfo(self, fake_dct=None):
        """Return a tuple containing the time left and a verbose string describing the current status.
        
        Returns:
            tuple:
                int: time left in seconds
                str: verbose description of status 

        Args:
            None

        Raises:
            ? QQQ

        """

        nowish = datetime.datetime.now()
        retdct = fake_dct if fake_dct else self.cached_smartups.result
        if retdct is None:
            return None
        assert(self._when_did_we_start_discharging is not None or self._when_did_we_start_recharging is not None)
        our_delta = nowish - (self._when_did_we_start_discharging if self._when_did_we_start_discharging is not None else self._when_did_we_start_recharging)
        seconds_since_discharging_began = our_delta.seconds
        initial_battery_level = self._what_was_battery_level_when_we_did_start_disch_or_rchgg
        current_battery_level = int(retdct['BATCAP'].strip('%'))
        battery_level_difference = initial_battery_level - current_battery_level
        time_taken_to_change_by_one_percentage_point = 0 if battery_level_difference == 0 else seconds_since_discharging_began / float(battery_level_difference)
        retdct['timeleft'] = None
        if current_battery_level == 100 and not self.discharging:
            self._verbose_werewechargingordischarging = 'neither'
            retdct['timeleft'] = 0
            retdct['verbose'] = "Battery is full and trickle-charging."
        elif initial_battery_level is None or time_taken_to_change_by_one_percentage_point == 0:
            retdct['verbose'] = "Battery is %s; currently at %d%%." % ("recharging" if self.charging else "discharging" if self.discharging else "trickling", current_battery_level)  # retdct['Vin' ] == 'GOOD' else "discharging" if current_battery_level < 100
        elif self.discharging:
            if current_battery_level not in self._our_timeremainingestimate_dct.keys():
                self._our_timeremainingestimate_dct[current_battery_level] = time_taken_to_change_by_one_percentage_point * (initial_battery_level - 20)
                print("As if by magik, the value is %d" % self._our_timeremainingestimate_dct[current_battery_level])
            retdct['timeleft'] = self._our_timeremainingestimate_dct[current_battery_level]
            self._verbose_werewechargingordischarging = 'discharging'
            if retdct['timeleft'] < 0:
                retdct['verbose'] = "EVERYBODY PANIC!!!!! BATTERY IS HELLA LOW."
            else:
                retdct['verbose'] = "Discharging. Battery at %d%%. Time until low battery: %s" % (current_battery_level, loworchargebattery_string_info(retdct['timeleft']))  # #                outstr = "In %d seconds, the battery level has fallen from %d%% to %d%%. Time to low battery: %s" % (seconds_since_discharging_began, initial_battery_level, current_battery_level, loworchargebattery_string_info(self._verbose_dct['timeleft']))
        elif self.charging:
            self._verbose_werewechargingordischarging = 'charging'  #        ['Vin'] == 'GOOD'
            if current_battery_level not in self._our_timeremainingestimate_dct.keys():
                self._our_timeremainingestimate_dct[current_battery_level] = -time_taken_to_change_by_one_percentage_point * (100 - current_battery_level)
                print("As if by magic, the value is %d" % self._our_timeremainingestimate_dct[current_battery_level])
            retdct['timeleft'] = self._our_timeremainingestimate_dct[current_battery_level]
            if retdct['timeleft'] < 0:
                retdct['timeleft'] = 999999999  # Battery level FELL, even though we're charging. WEIRD.
            retdct['verbose'] = "Charging. Battery at %d%%. Time until full: %s" % (current_battery_level, loworchargebattery_string_info(retdct['timeleft']))  #  #                outstr = "In %d seconds, the battery level has risen from %d%% to %d%%. Time to full: %s" % (seconds_since_discharging_began, initial_battery_level, current_battery_level, loworchargebattery_string_info(self._verbose_dct['timeleft']))
        else:
            retdct['verbose'] = "Recalculating..."
        return (retdct['timeleft'], retdct['verbose'])


SmartUPS = SmartUPSInterface(serial_device=identify_serial_device(), use_caching=True, pause_duration_between_uncached_reads=1)

