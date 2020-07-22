#!/usr/bin/python3

'''
smartupsconroller --- Python script to monitor the RPi UPSPack Standard V2

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


class Error(Exception):
    """Base class for other exceptions"""

    def __init__(self, message):
        super().__init__(message)


class InitializationError(Error):
    """Class for all initialization errors"""

    def __init__(self, message):
        super().__init__(message)


class CachingStructureInitializationError(InitializationError):
    """Class for all caching structure initialization errors"""

    def __init__(self, message):
        super().__init__(message)


class CachingStructurePrematureReadError(InitializationError):
    """Class for all caching structure premature read errors"""

    def __init__(self, message):
        super().__init__(message)


class SmartUPSInitializationError(InitializationError):
    """Class for all smart ups initialization errors"""

    def __init__(self, message):
        super().__init__(message)


class ReadError(Error):

    """Class for all read errors"""

    def __init__(self, message):
        super().__init__(message)


class ReadSmartUPSError(ReadError):

    """Class for all read-smart-ups errors"""

    def __init__(self, message):
        super().__init__(message)


class ReadOnlyError(ReadError):

    """Class for all read-only errors --- do not write"""

    def __init__(self, message):
        super().__init__(message)


class CachingError(Error):
    """Class for all caching errors"""

    def __init__(self, message):
        super().__init__(message)


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


class DummyCachingCall:

    def __init__(self, refreshfrequency, func, *args, **kwargs):
        self.__args = args
        self.__kwargs = kwargs
        self.__func = func
        del refreshfrequency
        super().__init__()

    def _update_me(self):
        pass

    @property
    def result(self):
        return self.__func(*self.__args, **self.__kwargs)


class SmartUPSInterface:

    def __init__(self, serial_device, use_caching=True, pause_duration_between_uncached_reads=1):
#         self.__serialdev_lck = ReadWriteLock()
        self.__smupsinfo_lck = ReadWriteLock()
        self.__battlevel_lck = ReadWriteLock()
        self.__smversion_lck = ReadWriteLock()
        self.__verbostxt_lck = ReadWriteLock()
        self.__time_left_lck = ReadWriteLock()
        self.__Volts_out_lck = ReadWriteLock()
        self.__dischargg_lck = ReadWriteLock()
        self.__charging_lock = ReadWriteLock()
        self.__serial_rx_lck = ReadWriteLock()
#         self.__serial_device = serial_device
        self.__timeleft_list = []
        self._last_time_we_read_smartups = None
        self._last_smartups_output = None
        self._when_did_we_start_discharging = None
        self._when_did_we_start_recharging = None
        self._what_was_battery_level_when_we_did_start_disch_or_rchgg = None
        self._verbose_werewechargingordischarging = None
        self._serial_iface = serial.Serial(
            port=serial_device,
            baudrate=9600,
            timeout=1,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS
        )
#         os.system("stty -F %s 9600 cs8 -cstopb -parenb" % self.__serial_device)
        self.__cached_smartups = DummyCachingCall(pause_duration_between_uncached_reads, self._forgivingly_read_smartups_output) \
                                if not use_caching else \
                                SelfCachingCall(pause_duration_between_uncached_reads, self._forgivingly_read_smartups_output)  # , self.serial_device)
        self.__cached_smartups._update_me()
#        self._wait_until_nonNone_cached_result()
        super().__init__()

    def _forgivingly_read_smartups_output(self):
        for attempts in range(10):
            try:
                res = self._read_smartups_output()
                return res
            except Exception:
                sleep_for_a_random_period(.5)
        raise ReadSmartUPSError("Attempted %d times to read the smartUPS output. Failed totally." % attempts)

    def _wait_until_nonNone_cached_result(self):
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
    def latest_serial_rx(self):
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

    @latest_serial_rx.setter
    def latest_serial_rx(self, value):
        raise ReadOnlyError("Cannot set cached_smartups attribute. That is inappropriate!")

    def _read_smartups_output(self):
        # FIXME: add a read-write lock for self._last_time_we_read_smartups etc.
        current_timestamp = datetime.datetime.now()
        if self._last_time_we_read_smartups is None or (current_timestamp - self._last_time_we_read_smartups).seconds >= 1:
            self._last_time_we_read_smartups = current_timestamp
            self._last_smartups_output = self.latest_serial_rx
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
                if self._verbose_werewechargingordischarging is None:
                    self._verbose_werewechargingordischarging = 'charging'
        else:
            if self._when_did_we_start_discharging is None:
                self._when_did_we_start_discharging = datetime.datetime.now()
                self._when_did_we_start_recharging = None
                self._what_was_battery_level_when_we_did_start_disch_or_rchgg = int(dct['BATCAP'])
                if self._verbose_werewechargingordischarging is None:
                    self._verbose_werewechargingordischarging = 'discharging'
        return dct

#     @property
#     def serial_device(self):
#         try:
#             self.__serialdev_lck.acquire_read()
#             retval = self.__serial_device
#         finally:
#             self.__serialdev_lck.release_read()
#         return retval
#
#     @serial_device.setter
#     def serial_device(self, value):
#         raise ReadOnlyError("Cannot set serial_device attribute. That is inappropriate!")

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
            except AttributeError:
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
            except CachingStructurePrematureReadError:
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

    @Vout.setter
    def Vout(self, value):
        raise ReadOnlyError("Cannot set Vout attribute. That is inappropriate!")

    @property
    def verbose(self):
        try:
            self.__verbostxt_lck.acquire_read()
            try:
                retval = self._return_meaningful_status()['verbose']  # TODO: make more OO, less 1960s
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
            i = self._return_meaningful_status()['timeleft']
            if i is None:
                retval = i
            else:
                self.__timeleft_list.insert(0, i)
                if len(self.__timeleft_list) >= 10:
                    _ = self.__timeleft_list.pop()
                retval = sum(self.__timeleft_list) // len(self.__timeleft_list)
        finally:
            self.__time_left_lck.release_read()
        return retval

    @timeleft.setter
    def timeleft(self, value):
        raise ReadOnlyError("Cannot set timeleft attribute. That is inappropriate!")

    def _return_meaningful_status(self):
        nowish = datetime.datetime.now()
        retdct = self.cached_smartups.result
        if retdct is None:
            return None
        assert(self._when_did_we_start_discharging is not None or self._when_did_we_start_recharging is not None)
        our_delta = nowish - (self._when_did_we_start_discharging if self._when_did_we_start_discharging is not None else self._when_did_we_start_recharging)
        seconds_since_discharging_began = our_delta.seconds
        initial_battery_level = self._what_was_battery_level_when_we_did_start_disch_or_rchgg
        current_battery_level = int(retdct['BATCAP'].strip('%'))
        battery_level_difference = initial_battery_level - current_battery_level
        time_taken_to_change_by_one_percentage_point = None if battery_level_difference == 0 else seconds_since_discharging_began / float(battery_level_difference)
        retdct['timeleft'] = None
        if current_battery_level == 100 and not self.discharging:
            self._verbose_werewechargingordischarging = 'neither'
            retdct['timeleft'] = 0
            retdct['verbose'] = "Battery is full and trickle-charging."
        elif initial_battery_level is None or time_taken_to_change_by_one_percentage_point is None:
            retdct['verbose'] = "Battery is %s; currently at %d%%." % ("recharging" if self.charging else "discharging" if self.discharging else "trickling", current_battery_level)  # retdct['Vin' ] == 'GOOD' else "discharging" if current_battery_level < 100
        elif self.discharging:
            retdct['timeleft'] = time_taken_to_change_by_one_percentage_point * (initial_battery_level - 20)
            self._verbose_werewechargingordischarging = 'discharging'
            if retdct['timeleft'] < 0:
                retdct['verbose'] = "EVERYBODY PANIC!!!!! BATTERY IS HELLA LOW."
            else:
                retdct['verbose'] = "Discharging. Battery at %d%%. Time until low battery: %s" % (current_battery_level, loworchargebattery_string_info(retdct['timeleft']))  # #                outstr = "In %d seconds, the battery level has fallen from %d%% to %d%%. Time to low battery: %s" % (seconds_since_discharging_began, initial_battery_level, current_battery_level, loworchargebattery_string_info(self._verbose_dct['timeleft']))
        elif self.charging:
            self._verbose_werewechargingordischarging = 'charging'  #        ['Vin'] == 'GOOD'
            retdct['timeleft'] = -time_taken_to_change_by_one_percentage_point * (100 - current_battery_level)
            retdct['verbose'] = "Charging. Battery at %d%%. Time until full: %s" % (current_battery_level, loworchargebattery_string_info(retdct['timeleft']))  #  #                outstr = "In %d seconds, the battery level has risen from %d%% to %d%%. Time to full: %s" % (seconds_since_discharging_began, initial_battery_level, current_battery_level, loworchargebattery_string_info(self._verbose_dct['timeleft']))
        else:
            retdct['verbose'] = "Recalculating..."
        return retdct


class ReadWriteLock:
    """ A lock object that allows many simultaneous "read locks", but
    only one "write lock." """

    def __init__(self):
        self._read_ready_lck = Lock()
        self._read_ready = Condition(self._read_ready_lck)
        self._readers = 0

    def locked(self):
        return self._read_ready_lck.locked()

    def acquire_read(self):
        """ Acquire a read lock. Blocks only if a thread has
        acquired the write lock. """
        self._read_ready.acquire()
        try:
            self._readers += 1
        finally:
            self._read_ready.release()

    def release_read(self):
        """ Release a read lock. """
        self._read_ready.acquire()
        try:
            self._readers -= 1
            if not self._readers:
                self._read_ready.notifyAll()
        finally:
            self._read_ready.release()

    def acquire_write(self):
        """ Acquire a write lock. Blocks until there are no
        acquired read or write locks. """
        self._read_ready.acquire()
        while self._readers > 0:
            self._read_ready.wait()

    def release_write(self):
        """ Release a write lock. """
        self._read_ready.release()


class SelfCachingCall:
    """Self-repeating call to function; saves result; caches it.

    SelfCachingCall() is a class instance that calls a specific function (with specified parameters)
    every N seconds. The result, including any error, is cached and is made available to the
    programmer. The call happens in the background. An instance of SelfCachingCall() encapsulates that
    functionality and caches the result of the call.

    e.g.
        >>> GVAR = 5
        >>> def myfunc(addme):
                global GVAR
                GVAR += addme
                return GVAR
        >>> from my.classes import SelfCachingCall
        >>> #................freq, func, paramsForfunc
        >>> c = SelfCachingCall(2, myfunc, 100)
        >>> c.result
        my.globals.exceptions.FrontendStillAwaitingCachedValue: We have not cached the first result yet
        >>> sleep(1); c.result
        605

    Note:
        If the programmer tries to read the cached value before the first call to the function,
        an exception will be thrown.

    Args:
        refreshfrequency (int): How often should I call the function
        func: What is the function?
        args,kwargs: Pass these parameters to the function

    Methods:
        _update_me(): Force a new call to the function; save the result in our cache.

    Attributes:
        result (int): result of most recent (cached) call to the function that's being cached
            FYI, if the most recent call threw an exception, then the act of getting the result
            attribute will throw that exception. I guess you could say the subroutine didn't
            only catch it; it cached it.

    Exceptions:
        FrontendStillAwaitingCachedValue: If we don't have a cached value yet, this exception is raised.

    """

    def __init__(self, refreshfrequency, func, *args, **kwargs):
        assert (isinstance(refreshfrequency, int)
                or isinstance(refreshfrequency, float))
        self.__args = args
        self.__kwargs = kwargs
        self.__func = func
        self.__refreshfrequency = refreshfrequency
        self.__refreshfreq_lock = ReadWriteLock()
        self.__result = None
        self.__error = CachingStructurePrematureReadError(
            'We have not cached the first result yet')
        self.__result_and_error_lock = ReadWriteLock()
        self.__time_to_join = False
        self.__update_lock = ReadWriteLock()
        self.__keepupdating_thread = Thread(target=self._keep_updating)
        self.__keepupdating_thread.daemon = True
        self.__keepupdating_thread.start()
        super().__init__()

    def _error(self):
        try:
            self.__result_and_error_lock.acquire_read()
            retval = self.__error
        finally:
            self.__result_and_error_lock.release_read()
        return retval

    def _keep_updating(self):
        time_left_before_update = 0
        while not self.__time_to_join:
            if time_left_before_update <= 0:
                self._update_me()
                time_left_before_update = self.__refreshfrequency
            else:
                sleep_for_how_long = min(1, time_left_before_update)
                time_left_before_update -= sleep_for_how_long
                sleep(sleep_for_how_long)
        print('No more soup for you')

#         self.join() # FIXME: Why was this commented out?!
    def _update_me(self):
        try:
            self.__update_lock.acquire_write()
            the_new_result = self.__func(*self.__args, **self.__kwargs)
            the_new_error = None
        except Exception as e:
            the_new_result = None
            the_new_error = e
        finally:
            self.__update_lock.release_write()
        try:
            self.__result_and_error_lock.acquire_write()
            self.__error = the_new_error
            self.__result = the_new_result
        finally:
            self.__result_and_error_lock.release_write()

    @property
    def result(self):
        try:
            self.__result_and_error_lock.acquire_write()
            while True:
                try:
                    retval = copy.deepcopy(self.__result)
                except RuntimeError:
                    print('value changed while iterating, or something; probably a race condition; retrying...')
                    sleep_for_a_random_period(.1)
                else:
                    reterr = self.__error
                    break
        except Exception as e:
            #             from my.globals.logging import Logger
            print('SelfCachingCall.result reported this ==> %s' % str(e))
            retval = None
            reterr = e
        finally:
            self.__result_and_error_lock.release_write()
        if reterr is not None:
            raise reterr
        else:
            return retval

    def join(self):
        self.__time_to_join = True
        self.__keepupdating_thread.join()

    @property
    def refreshfrequency(self):
        self.__refreshfreq_lock.acquire_read()
        retval = self.__refreshfrequency
        self.__refreshfreq_lock.release_read()
        return retval

    @refreshfrequency.setter
    def refreshfrequency(self, value):
        self.__refreshfreq_lock.acquire_write()
        self.__refreshfrequency = value
        self.__refreshfreq_lock.release_write()


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


def trythis():
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


SmartUPS = SmartUPSInterface(serial_device=identify_serial_device(), use_caching=True, pause_duration_between_uncached_reads=1)

'''

try:
    import serial
except ImportError as ex:
    raise ImportError("Please install pySerial module (Python 3)")
import time

ser = serial.Serial(
    port='/dev/ttyUSB0', 
    baudrate=9600, 
    timeout=1,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS
)



from smartupscontroller import *
trythis()

SmartUPS.verbose
SmartUPS.batterylevel
SmartUPS.discharging
SmartUPS.charging
SmartUPS.Vout
#SmartUPS._serial_iface
from time import sleep
while True:
    print("Vout=%1.4f; charging?%s; discharging?%s; batterylevel=%d%%; timeleft=%s; verbose=%s" % (SmartUPS.Vout, 'Yes' if SmartUPS.charging else 'No', 
                        'Yes' if SmartUPS.discharging else 'No', SmartUPS.batterylevel, ((str(SmartUPS.timeleft//60) + 'm') if SmartUPS.timeleft is not None else '?'), SmartUPS.verbose))
    sleep(5)

    

serial_device = identify_serial_device()
read_smartups_output(serial_device)

SmartUPS.batterylevel
SmartUPS.discharging
SmartUPS.charging
SmartUPS.Vout

'''

