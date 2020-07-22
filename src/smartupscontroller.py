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

from my_exceptions import ReadSmartUPSError, ReadOnlyError, CachingStructureInitializationError


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
        self.__serial_device = serial_device
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


SmartUPS = SmartUPSInterface(serial_device=identify_serial_device(), use_caching=True, pause_duration_between_uncached_reads=1)

