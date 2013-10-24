#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Copyright 2013 Develer S.r.l. (http://www.develer.com/)
# All rights reserved.
#
# Author: Lorenzo Villani <lvillani@develer.com>
# Author: Riccardo Ferrazzo <rferrazz@develer.com>
#

import sys

from ctypes import pointer, sizeof, c_uint32

from c_wrapper import *

#
# Object oriented interface
#

class TurboActivate(object):
    def __init__(self, dat_file, guid, use_trial=False, library_folder=""):
        self.mode = TA_USER

        self._dat_file = wstr(dat_file)
        self._guid = wstr(guid)
        self._lib = load_library(library_folder)

        self._check_call(self._lib.PDetsFromPath, self._dat_file)

        if use_trial:
            self._check_call(self._lib.UseTrial, self.mode)

    #
    # Public
    #

    # Product key

    def product_key(self):
        buf_size = 128
        try:
            buf = wbuf(buf_size)
            self._check_call(self._lib.GetPKey, buf, buf_size)
            return buf.value
        except TurboActivateProductKeyError as e:
            return None

    def set_product_key(self, product_key):
        try:
            self._check_call(self._lib.CheckAndSavePKey, wstr(product_key), self.mode)
        except TurboActivateError as e:
            raise e

    # Activation status

    def deactivate(self, erase_p_key=True):
        e = '1' if erase_p_key else '0'
        self._check_call(self._lib.Deactivate, e)

    def activate(self, extra_data=""):
        if self.is_activated():
            return False
        fn = self._lib.Activate
        args = []
        try:
            self._check_call(fn, *args)
            return True
        except TurboActivateError:
            self.deactivate(True)
            return False

    def is_activated(self):
        try:
            self._check_call(self._lib.IsActivated, self._guid)

            return True
        except TurboActivateError:
            return False

    def is_genuine(self, options=None):
        fn = self._lib.IsGenuine
        args = [self._guid]
        try:
            self._check_call(fn, *args)

            return True
        except TurboActivateFeaturesChangedError:
            return True
        except TurboActivateError:
            return False

    # Trial

    def is_trial_ongoing(self):
        return self.trial_remaining_days() > 0

    def trial_remaining_days(self):
        days = c_uint32(0)
        ret = self._lib.TrialDaysRemaining(self._guid, days)

        if ret != TA_OK:
            raise TurboActivateError()

        return days.value

    def extend_trial(self, extension_code):
        self._check_call(self._lib.ExtendTrial, extension_code)

    # License flags

    def refresh_license_flags(self):
        try:
            self._check_call(self._lib.IsGenuine, self._guid)
        except TurboActivateFeaturesChangedError:
            # This is expected.
            pass
        except TurboActivateError as e:
            raise e

    #
    # Private
    #

    def _check_call(self, callable, *args):
        return_code = callable(*args)

        # All ok, no need to perform error handling.
        if return_code == TA_OK:
            return

        # Raise an exception type appropriate for the kind of error
        if return_code == TA_E_FEATURES_CHANGED:
            raise TurboActivateFeaturesChangedError()
        elif return_code == TA_E_PDETS:
            raise TurboActivateDatFileError()
        elif return_code == TA_E_PKEY:
            raise TurboActivateProductKeyError()


        # Otherwise bail out and raise a generic exception
        raise TurboActivateError()


#
# Exception types
#

class TurboActivateError(Exception):
    pass


class TurboActivateFeaturesChangedError(TurboActivateError):
    pass


class TurboActivateGuidNotSetError(TurboActivateError):
    pass


class TurboActivateDatFileError(TurboActivateError):
    pass

class TurboActivateProductKeyError(TurboActivateError):
    pass

