from .. import *
from . import API_KEY, API_SECRET

import functools
import sys
import types

from libcloud.dns.providers import get_driver

from dnsmadeeasy.driver import DNSMadeEasyDNSDriver

Driver = get_driver('dnsmadeeasy')

def drivertest(f):
    """Marks a function as a test for the DNS driver"""
    @functools.wraps(f)
    def inner():
        try:
            return f(Driver(API_KEY, API_SECRET, True))
        except DNSMadeEasyRateLimitExceededError as e:
            printf('Rate limit exceeded (0 of %d requests remaining); '
                    'terminating prematuely', e.request_limit)
            sys.exit(2)
    return test(inner)


@test
def DNSMadeEasyDNSDriver_registered():
    """Tests that the driver is registered"""
    assert_eq(
        Driver,
        DNSMadeEasyDNSDriver)
