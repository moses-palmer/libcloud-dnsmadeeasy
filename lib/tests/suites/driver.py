from .. import *

from libcloud.dns.providers import get_driver

from dnsmadeeasy.driver import DNSMadeEasyDNSDriver

Driver = get_driver('dnsmadeeasy')


@test
def DNSMadeEasyDNSDriver_registered():
    """Tests that the driver is registered"""
    assert_eq(
        Driver,
        DNSMadeEasyDNSDriver)
