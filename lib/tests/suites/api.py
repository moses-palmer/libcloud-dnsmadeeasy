from .. import *
from . import API_KEY, API_SECRET

from dnsmadeeasy.api import Headers


@test
def Headers_items0():
    """Tests that all required keys are present in headers"""
    assert_eq(
        sorted(k for k, v in Headers(API_KEY, API_SECRET).items()),
        ['x-dnsme-apiKey', 'x-dnsme-hmac', 'x-dnsme-requestDate'])


@test
def Headers_items1():
    """Tests that the API key is correctly set"""
    assert_eq(
        dict(Headers(API_KEY, API_SECRET).items())['x-dnsme-apiKey'],
        API_KEY)
