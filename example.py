#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from turboactivate import (
    TurboActivate,
    GenuineOptions,
    TA_SKIP_OFFLINE,
    TurboActivateError,
    TurboActivateTrialUsedError,
    TurboActivateConnectionError,
    TurboActivateTrialExpiredError,
    TurboActivateTrialCorruptedError,
    TurboActivateConnectionDelayedError
)

# TODO: paste your Version GUID here.
TA_GUID = "18324776654b3946fc44a5f3.49025204"

# TODO: paste the path to your dat file here
TA_DAT = "TurboActivate.dat"

if __name__ == "__main__":
    ta = TurboActivate(TA_DAT, TA_GUID, use_trial=True)
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
        ta.is_genuine(opts)
    except (TurboActivateConnectionDelayedError, TurboActivateConnectionError) as e:
        print(
            "YourApp is activated, but it failed to verify the activation with the LimeLM servers. You can still use the app for the duration of the grace period.")

        raise e
    except TurboActivateError:
        print("Not activated")

    # TODO: prompt the user for a product key
    try:
        ta.set_product_key("U9MM-4NJ5-QFG8-TWM5-QM75-92YI-NETA")
    except TurboActivateError as e:
        print("key failed to save")

        raise e

    print("Product key saved successfully.")

    ta.activate()

    print ("Activated successfully.")

    # if this app is activated then you can get a feature value (completely optional)
    # See: http://wyday.com/limelm/help/license-features/
    #
    # feature_value = ta.get_feature_value("myFeature")
    # print("the value of myFeaure is %s" % feature_value)
