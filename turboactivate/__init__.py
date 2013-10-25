#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
    def __init__(self, dat_file, guid, use_trial=False, library_folder="", mode=TA_USER):
        self._mode = mode
        self._dat_file = wstr(dat_file)
        self._guid = wstr(guid)
        self._lib = load_library(library_folder)

        self._check_call(self._lib.PDetsFromPath, self._dat_file)

        if use_trial:
            self._check_call(self._lib.UseTrial, self._mode)

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
            self._check_call(self._lib.CheckAndSavePKey, wstr(product_key), self._mode)
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
            fn = self._lib.ActivationRequestToFileEx if activation_request_file else self._lib.ActivateEx
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
        """Gets the extra data you passed in using activate()"""
        buf_size = 255
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

    def trial_days_remaining(self):
        """
        Get the number of trial days remaining.
        0 days if the trial has expired or has been tampered with
        (1 day means *at most* 1 day, that is it could be 30 seconds)
        
        You must have instantiated TurboActivate with the use_trial 
        flag to use this function 
        """
        days = c_uint32(0)
        self._check_call(self._lib.TrialDaysRemaining, self._guid, pointer(days))
        return days.value

    def extend_trial(self, extension_code):
        """Extends the trial using a trial extension created in LimeLM."""
        self._check_call(self._lib.ExtendTrial, wstr(extension_code))

    # Utils

    def is_date_valid(self, date, flags=0):
        """
        Checks if the string in the form "YYYY-MM-DD HH:mm:ss" is a valid
        date/time. The date must be in UTC time and "24-hour" format. If your
        date is in some other time format first convert it to UTC time before
        passing it into this function.
        """
        try:
            self._check_call(self._lib.IsDateValid, wstr(date), flags)
            return True
        except TurboActivateFlagsError as e:
            raise e
        except TurboActivateError:
            return False

    def set_custom_path(self, path):
        """
        This function allows you to set a custom folder to store the activation
        data files. For normal use we do not recommend you use this function.
        
        Only use this function if you absolutely must store data into a separate
        folder. For example if your application runs on a USB drive and can't write
        any files to the main disk, then you can use this function to save the activation
        data files to a directory on the USB disk.
        
        If you are using this function (which we only recommend for very special use-cases)
        then you must call this function on every start of your program at the very top of
        your app before any other functions are called.
        
        The directory you pass in must already exist. And the process using TurboActivate
        must have permission to create, write, and delete files in that directory.
        """
        self._check_call(self._lib.SetCustomActDataPath, wstr(path))

    def set_custom_proxy(self, address):
        """
        Sets the custom proxy to be used by functions that connect to the internet.
        
        Proxy address in the form: http://username:password@host:port/
        
        Example 1 (just a host): http://127.0.0.1/
        Example 2 (host and port): http://127.0.0.1:8080/
        Example 3 (all 3): http://user:pass@127.0.0.1:8080/
        
        If the port is not specified, TurboActivate will default to using port 1080 for proxies.
        """
        self._check_call(self._lib.SetCustomProxy, wstr(address))

    #
    # Private
    #

    def _check_call(self, callable, *args):
        return_code = callable(*args)

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
        elif return_code == TA_E_EDATA_LONG:
            raise TurboActivateExtraDataLongError()
        elif return_code == TA_E_PKEY:
            raise TurboActivateProductKeyError()
        elif return_code == TA_E_INUSE:
            raise TurboActivateInUseError()
        elif return_code == TA_E_REVOKED:
            raise TurboActivateRevokedError()
        elif return_code == TA_E_GUID:
            raise TurboActivateGuidError()
        elif return_code == TA_E_TRIAL:
            raise TurboActivateTrialCorruptedError()
        elif return_code == TA_E_TRIAL_EUSED:
            raise TurboActivateTrialUsedError()
        elif return_code == TA_E_TRIAL_EEXP:
            raise TurboActivateTrialExpiredError()
        elif return_code == TA_E_ACTIVATE:
            raise TurboActivateNotActivatedError()
        elif return_code == TA_E_INVALID_FLAGS:
            raise TurboActivateFlagsError()
        elif return_code == TA_E_COM:
            raise TurboActivateComError()
        elif return_code == TA_E_INET:
            raise TurboActivateConnectionError()
        elif return_code == TA_E_INET_DELAYED:
            raise TurboActivateConnectionDelayedError()
        elif return_code == TA_E_PERMISSION:
            raise TurboActivatePermissionError()

        # Otherwise bail out and raise a generic exception
        raise TurboActivateError()


#
# Exception types
#

class TurboActivateError(Exception):
    """Generic TurboActivate error"""
    pass


class TurboActivateFailError(TurboActivateError):
    """Fail error"""
    pass


class TurboActivateProductKeyError(TurboActivateError):
    """Invalid product key"""
    pass


class TurboActivateNotActivatedError(TurboActivateError):
    """The product needs to be activated."""
    pass


class TurboActivateConnectionError(TurboActivateError):
    """Connection to the server failed."""
    pass


class TurboActivateInUseError(TurboActivateError):
    """The product key has already been activated with the maximum number of computers."""
    pass


class TurboActivateRevokedError(TurboActivateError):
    """The product key has been revoked."""
    pass


class TurboActivateGuidError(TurboActivateError):
    """The version GUID doesn't match that of the product details file."""
    pass


class TurboActivateTrialCorruptedError(TurboActivateError):
    """The trial data has been corrupted, using the oldest date possible."""
    pass


class TurboActivateTrialUsedError(TurboActivateError):
    """The trial extension has already been used."""
    pass


class TurboActivateTrialExpiredError(TurboActivateError):
    """
    The activation has expired or the system time has been tampered
    with. Ensure your time, timezone, and date settings are correct.
    """
    pass


class TurboActivateComError(TurboActivateError):
    """
    The hardware id couldn't be generated due to an error in the COM setup.
    Re-enable Windows Management Instrumentation (WMI) in your group policy
    editor or reset the local group policy to the default values. Contact
    your system admin for more information.
    
    This error is Windows only.
    
    This error can also be caused by the user (or another program) disabling
    the "Windows Management Instrumentation" service. Make sure the "Startup type"
    is set to Automatic and then start the service.
    
    
    To further debug WMI problems open the "Computer Management" (compmgmt.msc),
    expand the "Services and Applications", right click "WMI Control" click
    "Properties" and view the status of the WMI.
    """
    pass


class TurboActivatePermissionError(TurboActivateError):
    """
    Insufficient system permission. Either start your process as an
    admin / elevated user or call the function again with the
    TA_USER flag instead of the TA_SYSTEM flag.
    """
    pass

class TurboActivateFeaturesChangedError(TurboActivateError):
    """
    If IsGenuine() or IsGenuineEx() reactivated and the features
    have changed, then this will be the return code. Treat this
    as a success.
    """
    pass


class TurboActivateDatFileError(TurboActivateError):
    """The product details file "TurboActivate.dat" failed to load."""
    pass


class TurboActivateFlagsError(TurboActivateError):
    """
    The flags you passed to use_trial(...) were invalid (or missing).
    """
    pass

class TurboActivateExtraDataLongError(TurboActivateError):
    """
    The "extra data" was too long. You're limited to 255 UTF-8 characters.
    Or, on Windows, a Unicode string that will convert into 255 UTF-8
    characters or less.
    """
    pass


class TurboActivateConnectionDelayedError(TurboActivateError):
    """
    is_genuine() previously had a TA_E_INET error, and instead
    of hammering the end-user's network, is_genuine() is waiting
    5 hours before rechecking on the network.
    """
    pass

