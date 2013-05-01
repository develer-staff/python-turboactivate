#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Copyright 2013 Develer S.r.l. (http://www.develer.com/)
# All rights reserved.
#
# Author: Lorenzo Villani <lvillani@develer.com>
#

from ctypes import c_uint32

from turboactivate.c_api import CheckAndSavePKey, \
    Deactivate, \
    ExtendTrial, \
    IsGenuine, \
    IsActivated, \
    PDetsFromPath, \
    TrialDaysRemaining, \
    UseTrial, \
    TA_E_FEATURES_CHANGED, \
    TA_E_PDETS, \
    TA_OK, \
    TA_USER, \
    POINTER


#
# Object oriented interface
#

class TurboActivate(object):
    def __init__(self, dat_file, guid, use_trial=False):
        super(TurboActivate, self).__init__()

        self.dat_file = dat_file
        self.guid = guid

        self._check_call(PDetsFromPath, dat_file)

        if use_trial:
            self._check_call(UseTrial, TA_USER)

    #
    # Public
    #

    # Product key

    def product_key(self):
        return "STUB"

    def set_product_key(self, product_key):
        try:
            self._check_call(CheckAndSavePKey, product_key, TA_USER)
        except TurboActivateError as e:
            self.deactivate()

            raise e

    # Activation status

    def deactivate(self):
        self._check_call(Deactivate, True)

    def is_activated(self):
        try:
            self._check_call(IsActivated, self.guid)

            return True
        except TurboActivateError:
            return False

    def is_genuine(self):
        try:
            self._check_call(IsGenuine, self.guid)

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
        ret = TrialDaysRemaining(self.guid, days)

        if ret != TA_OK:
            raise TurboActivateError()

        return days.value

    def extend_trial(self, extension_code):
        self._check_call(ExtendTrial, extension_code)

    # License flags

    def refresh_license_flags(self):
        try:
            self._check_call(IsGenuine, self.guid)
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
