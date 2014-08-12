# -*- coding: utf-8 -*-
#
# Copyright 2013, 2014 Develer S.r.l. (http://www.develer.com/)
#
# Author: Lorenzo Villani <lvillani@develer.com>
# Author: Riccardo Ferrazzo <rferrazz@develer.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import sys
from os import path as ospath
from ctypes import (
    cdll,
    c_uint,
    c_char_p,
    c_wchar_p,
    Structure,
    create_string_buffer,
    create_unicode_buffer
)

# Utilities

wbuf = create_unicode_buffer if sys.platform == "win32" else create_string_buffer

wstr = c_wchar_p if sys.platform == "win32" else c_char_p

# Wrapper

TA_OK = 0x00000000
TA_FAIL = 0x00000001
TA_E_PKEY = 0x00000002
TA_E_ACTIVATE = 0x00000003
TA_E_INET = 0x00000004
TA_E_INUSE = 0x00000005
TA_E_REVOKED = 0x00000006
TA_E_GUID = 0x00000007
TA_E_PDETS = 0x00000008
TA_E_TRIAL = 0x00000009
TA_E_TRIAL_EUSED = 0x0000000C
TA_E_TRIAL_EEXP = 0x0000000D
TA_E_EXPIRED = 0x0000000D
TA_E_REACTIVATE = 0x0000000A
TA_E_COM = 0x0000000B
TA_E_INSUFFICIENT_BUFFER = 0x0000000E
TA_E_PERMISSION = 0x0000000F
TA_E_INVALID_FLAGS = 0x00000010
TA_E_IN_VM = 0x00000011
TA_E_EDATA_LONG = 0x00000012
TA_E_INVALID_ARGS = 0x00000013
TA_E_KEY_FOR_TURBOFLOAT = 0x00000014
TA_E_INET_DELAYED = 0x00000015
TA_E_FEATURES_CHANGED = 0x00000016
TA_E_ANDROID_NOT_INIT = 0x00000017

# Flags for the UseTrial() and CheckAndSavePKey() functions.

TA_SYSTEM = 0x00000001
TA_USER = 0x00000002

# Flags for the IsGeninueEx() function.

TA_SKIP_OFFLINE = 0x00000001
"""
If the user activated using offline activation
(ActivateRequestToFile(), ActivateFromFile() ), then with this
flag IsGenuineEx() will still try to validate with the LimeLM
servers, however instead of returning TA_E_INET (when within the
grace period) or TA_FAIL (when past the grace period) it will
instead only return TA_OK (if IsActivated()).

If you still want to get the TA_E_INET error code, without
deactivating after the grace period has expired, then use
this flag in tandem with TA_OFFLINE_SHOW_INET_ERR.

If the user activated using online activation then this flag
is ignored.
"""

TA_OFFLINE_SHOW_INET_ERR = 0x00000002
"""
If the user activated using offline activation, and you're
using this flag in tandem with TA_SKIP_OFFLINE, then IsGenuineEx()
will return TA_E_INET on internet failure instead of TA_OK.

If the user activated using online activation then this flag
is ignored.
"""

TA_DISALLOW_VM = 0x00000004
"""
Use the TA_DISALLOW_VM in UseTrial() to disallow trials in virtual machines.
If you use this flag in UseTrial() and the customer's machine is a Virtual
Machine, then UseTrial() will return TA_E_IN_VM.
"""

# Flags for the is_date_valid() Function

TA_HAS_NOT_EXPIRED = 0x00000001


class GENUINE_OPTIONS(Structure):
    _fields_ = [
        ("nLength", c_uint),
        ("flags", c_uint),
        ("nDaysBetweenChecks", c_uint),
        ("nGraceDaysOnInetErr", c_uint),
    ]


class ACTIVATE_OPTIONS(Structure):
    _fields_ = [
        ("nLength", c_uint),
        ("sExtraData", wstr),
    ]


def load_library(path):
    LIBRARIES = {
        'linux2': ospath.join(path, 'libTurboActivate.so'),
        'darwin': ospath.join(path, 'libTurboActivate.dylib'),
        'win32': ospath.join(path, 'TurboActivate.dll'),
    }

    return cdll.LoadLibrary(LIBRARIES[sys.platform])


def validate_result(return_code):
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
