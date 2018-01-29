#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013-2018 Develer S.r.l. (https://www.develer.com/)
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

from __future__ import absolute_import, division, print_function, unicode_literals

from turboactivate import (
    TurboActivate,
    GenuineOptions,
    TA_SKIP_OFFLINE,
    TurboActivateError,
    TurboActivateConnectionError,
    TurboActivateConnectionDelayedError
)

# TODO: paste your Version GUID here.
TA_GUID = ""

# TODO: paste the path to your dat file here
TA_DAT = "TurboActivate.dat"

if __name__ == "__main__":
    assert TA_DAT
    assert TA_GUID

    ta = TurboActivate(TA_DAT, TA_GUID)
    ta.use_trial()

    trial_days = ta.trial_days_remaining()

    print("Trial days remaining %d" % trial_days)

    opts = GenuineOptions()

    # How often to verify with the LimeLM servers (90 days)
    opts.days_between_checks(90)

    # The grace period if TurboActivate couldn't connect to the servers.
    # after the grace period is over IsGenuinEx() will return TA_FAIL instead of
    # TA_E_INET or TA_E_INET_DELAYED
    opts.grace_days(14)

    # In this example we won't show an error if the activation
    # was done offline by passing the TA_SKIP_OFFLINE flag
    opts.flags(TA_SKIP_OFFLINE)

    try:
        print('Is Genuine:', ta.is_genuine())
    except (TurboActivateConnectionDelayedError, TurboActivateConnectionError):
        print("App is activated, but it failed to verify the activation with the LimeLM servers. "
              "You can still use the app for the duration of the grace period.")
    except TurboActivateError:
        print("Not activated")

    try:
        ta.set_product_key(raw_input('Product Key: '))
        print("Product key saved successfully.")
    except TurboActivateError as e:
        print("Couldn't save product key.")
        raise e

    ta.activate()
    print("Activated successfully.")

    # if this app is activated then you can get a feature value (completely optional)
    # See: http://wyday.com/limelm/help/license-features/
    #
    # feature_value = ta.get_feature_value("myFeature")
    # print("the value of myFeaure is %s" % feature_value)
