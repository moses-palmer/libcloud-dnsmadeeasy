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


def domain_names():
    """Yields a list of domain names unique for this session"""
    i = 1
    while True:
        yield 'example%02d.com' % i
        i += 1

domain_names = domain_names()


@test
def DNSMadeEasyDNSDriver_registered():
    """Tests that the driver is registered"""
    assert_eq(
        Driver,
        DNSMadeEasyDNSDriver)


@drivertest
def DNSMadeEasyDNSDriver_list_zones0(d):
    """Tests that DNSMadeEasyDNSDriver.list_zones returns a sequence"""
    assert isinstance(d.list_zones(), types.ListType), \
        'DNSMadeEasyDNSDriver.list_zones did not return a list'
