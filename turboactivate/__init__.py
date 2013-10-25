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

class GenuineOptions(object):
    """A set of options to use with is_genuine()"""

    def __init__(self, flags=0, grace_days=0, days_between_checks=0):
        self._flags = flags
        self._grace_days = grace_days
        self._days_between_checks = days_between_checks

    def get_pointer(self):
        options = GENUINE_OPTIONS(sizeof(GENUINE_OPTIONS()),
                                   self._flags,
                                   self._days_between_checks,
                                   self._grace_days)
        return pointer(options)

    def flags(self, flags):
        self._flags = flags

    def grace_days(self, days):
        """How often to contact the LimeLM servers for validation. 90 days recommended."""
        self._grace_days = days

    def days_between_checks(self, days):
        """
        If the call fails because of an internet error,
        how long, in days, should the grace period last (before
        returning deactivating and returning TA_FAIL).

        14 days is recommended.
        """
        self._days_between_checks = days


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
        """
        Gets the stored product key. NOTE: if you want to check if a product key is valid
        simply call is_product_key_valid().
        """
        buf_size = 128
        buf = wbuf(buf_size)
        try:
            self._check_call(self._lib.GetPKey, buf, buf_size)
            return buf.value
        except TurboActivateProductKeyError as e:
            return None

    def set_product_key(self, product_key):
        """Checks and saves the product key."""
        try:
            self._check_call(self._lib.CheckAndSavePKey, wstr(product_key), self.mode)
        except TurboActivateError as e:
            raise e

    def blacklists_keys(self, keys_list=[]):
        """
        Blacklists keys so they are no longer valid. Use "BlackListKeys" only if
        you're using the "Serial-only plan" in LimeLM. Otherwise revoke keys.
        """
        l = "".join(s for s in keys_list)
        self._check_call(self._lib.BlackListsKeys, l, len(keys_list))

    def is_product_key_valid(self):
        """
        Checks if the product key installed for this product is valid. This does NOT check if
        the product key is activated or genuine. Use is_activated() and is_genuine() instead.
        """
        try:
            self._check_call(self._lib.IsProductKeyValid, self._guid)
            return True
        except TurboActivateError:
            return False

    # Activation status

    def deactivate(self, erase_p_key=True, deactivation_request_file=""):
        """
        Deactivates the product on this computer. Set erase_p_key to True to erase the stored
        product key, False to keep the product key around. If you're using deactivate to let
        a user move between computers it's almost always best to *not* erase the product
        key. This way you can just use activate() when the user wants to reactivate
        instead of forcing the user to re-enter their product key over-and-over again.
        If deactivation_request_file is specified, then it gets the "deactivation request" 
        file for offline deactivation.
        """
        e = '1' if erase_p_key else '0'
        fn = self._lib.DeactivationRequestToFile if deactivation_request_file else self._lib.Deactivate
        args = [wstr(deactivation_request_file)] if deactivation_request_file else []
        args.append(e)
        try:
            self._check_call(fn, *args)
        except TurboActivateNotActivatedError:
            return

    def activate(self, extra_data="", activation_request_file=""):
        """
        Activates the product on this computer. You must call set_product_key()
        with a valid product key or have used the TurboActivate wizard sometime
        before calling this function.
        If activation_request_file is specified, then it gets the "activation request"
        file for offline activation.
        """
        if self.is_activated():
            return False
        fn = self._lib.ActivationRequestToFile if activation_request_file else self._lib.Activate
        args = [wstr(activation_request_file)] if activation_request_file else []
        if extra_data:
            fn = self._lib.ActivationRequestToFileEx if activation_request_file else self.__lib.ActivateEx
            options = ACTIVATE_OPTIONS(sizeof(ACTIVATE_OPTIONS()),
                                       wstr(extra_data))
            args.append(pointer(options))
        try:
            self._check_call(fn, *args)
            return True
        except TurboActivateError as e:
            if not activation_request_file:
                self.deactivate(True)
                return False
            raise e

    def activate_from_file(self, filename):
        """Activate from the "activation response" file for offline activation."""
        self._check_call(self._lib.ActivateFromFile, wstr(filename))

    def get_extra_data(self):
        buf_size = 128
        """Gets the extra data you passed in using activate()"""
        buf = wbuf(buf_size)
        try:
            self._check_call(self._lib.GetExtraData, buf, buf_size)
            return buf.value
        except TurboActivateFailError:
            return ""

    def is_activated(self):
        """ Checks whether the computer has been activated."""
        try:
            self._check_call(self._lib.IsActivated, self._guid)

            return True
        except TurboActivateError:
            return False

    # Features

    def get_feature_value(self, name):
        """Gets the value of a feature."""
        buf_size = 128
        buf = wbuf(buf_size)
        self._check_call(self._lib.GetFeatureValue, wstr(name), buf, buf_size)
        return buf.value

    def is_genuine(self, options=None):
        """
        Checks whether the computer is genuinely activated by verifying with the LimeLM servers.
        If reactivation is needed then it will do this as well.
        Optionally you can pass a GenuineOptions object to specify more details
        """
        fn = self._lib.IsGenuine
        args = [self._guid]
        if options:
            fn = self._lib.IsGenuineEx
            args.append(options.get_pointer())
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
        """
        Get the number of trial days remaining.
        0 days if the trial has expired or has been tampered with
        (1 day means *at most* 1 day, that is it could be 30 seconds)
        
        You must have instantiated TurboActivate with the use_trial 
        flag to use this function 
        """
        days = c_uint32(0)
        ret = self._lib.TrialDaysRemaining(self._guid, days)

        if ret != TA_OK:
            raise TurboActivateError()

        return days.value

    def extend_trial(self, extension_code):
        self._check_call(self._lib.ExtendTrial, extension_code)

    # License flags

    def refresh_license_flags(self):
        """Extends the trial using a trial extension created in LimeLM."""
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
        print return_code

        # All ok, no need to perform error handling.
        if return_code == TA_OK:
            return

        # Raise an exception type appropriate for the kind of error
        if return_code == TA_FAIL:
            raise TurboActivateFailError()
        elif return_code == TA_E_FEATURES_CHANGED:
            raise TurboActivateFeaturesChangedError()
        elif return_code == TA_E_PDETS:
            raise TurboActivateDatFileError()
        elif return_code == TA_E_PKEY:
            raise TurboActivateProductKeyError()
        elif return_code == TA_E_INUSE:
            raise TurboActivateInUseError()
        elif return_code == TA_E_ACTIVATE:
            raise TurboActivateNotActivatedError()

        # Otherwise bail out and raise a generic exception
        raise TurboActivateError()


#
# Exception types
#

class TurboActivateError(Exception):
    pass


class TurboActivateFailError(TurboActivateError):
    pass


class TurboActivateFeaturesChangedError(TurboActivateError):
    pass


class TurboActivateGuidNotSetError(TurboActivateError):
    pass


class TurboActivateDatFileError(TurboActivateError):
    pass


class TurboActivateProductKeyError(TurboActivateError):
    pass


class TurboActivateInUseError(TurboActivateError):
    pass


class TurboActivateNotActivatedError(TurboActivateError):
    pass

