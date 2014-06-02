# coding: utf-8
# libcloud-dnsmadeeasy
# Copyright (C) 2014 Moses Palmér
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.

import re
import requests

from libcloud.common.types import LibcloudError
from libcloud.dns.base import DNSDriver, Zone
from libcloud.dns.providers import set_driver
from libcloud.dns.types import RecordType

from .api import DNSMadeEasyAPI


class DNSMadeEasyRateLimitExceededError(LibcloudError):
    error_type = 'DNSMadeEasyRateLimitExceededError'
    kwargs = ('requests_remaining')

    def __init__(self, value, driver, request_limit):
        self.request_limit = request_limit
        super(DNSMadeEasyRateLimitExceededError, self).__init__(value = value,
            driver = driver)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return '<%s in %s, request_limit = %d, value = %s>' % (
            self.error_type, repr(self.driver), self.request_limit, self.value)


class DNSMadeEasyDNSDriver(DNSDriver):
    """
    DNSMadeEasy DNS driver.
    """
    name = 'DNSMadeEasy'
    website = 'http://dnsmadeeasy.com'

    RECORD_TYPE_MAP = {
        'ANAME': 'ANAME',
        RecordType.A: 'A',
        RecordType.AAAA: 'AAAA',
        RecordType.CNAME: 'CNAME',
        RecordType.MX: 'MX',
        RecordType.NS: 'NS',
        RecordType.PTR: 'PTR',
        RecordType.REDIRECT: 'HTTPRED',
        RecordType.SOA: 'SOA',
        RecordType.SPF: 'SPF',
        RecordType.SRV: 'SRV',
        RecordType.TXT: 'TXT'}

    ERROR_CODE_RE = re.compile(r'DE([0-9]+)\s*-\s*(.*)')

    class ParsedError(Exception):
        """A class used to pass parsed errors.
        """
        pass

    def _raise_for_response(self, r):
        """Raises a libcloud exception based on the server response.

        If no error has occurred, this method does nothing.

        If the error is unknown, a :exc:`requests.exceptions.HTTPError` is
        raised.

        :param requests.Response r: The server response.
        """
        try:
            r.raise_for_status()

        except requests.HTTPError as e:
            if r.status_code == 400:
                # Handle the request limit error here
                requests_remaining = r.headers.get('x-dnsme-requestsRemaining',
                    '')
                if requests_remaining and int(requests_remaining) == 0:
                    request_limit = r.headers.get('x-dnsme-requestLimit', '0')
                    raise DNSMadeEasyRateLimitExceededError(r, self,
                        request_limit)

                # Try to extract the error; this may fail since DNSMadeEasy may
                # not necessarily return proper JSON
                try:
                    e = r.json().get('error', ['unknown'])
                except:
                    raise e

                m = self.ERROR_CODE_RE.match(e[0])
                if m:
                    raise self.ParsedError(int(m.group(1)), m.group(2))
                else:
                    raise LibcloudError(e, self)

            raise

    def _to_zone(self, item):
        """Converts a DNSMadeEasy zone response item to a ``Zone`` instance.

        :param dict item: The response item.

        :return: a zone
        :rtype: libcloud.dns.base.Zone
        """
        return Zone(
            id = str(item['id']),
            domain = item['name'],
            type = 'master',
            ttl = None,
            driver = self,
            extra = {key: value
                for key, value in item.items()
                if not key in ('id', 'name')})

    def __init__(self, api_key, api_secret, sandbox = False):
        self._api = DNSMadeEasyAPI(api_key, api_secret, sandbox)

    def list_record_types(self):
        return list(self.RECORD_TYPE_MAP.keys())

    def list_zones(self):
        r = self._api.dns.managed.GET()
        self._raise_for_response(r)

        items = r.json()['data']
        return [self._to_zone(item)
            for item in items]

    def list_records(self, zone):
        raise NotImplementedError()

    def get_zone(self, zone_id):
        raise NotImplementedError()

    def get_record(self, zone_id, record_id):
        raise NotImplementedError()

    def create_zone(self, domain, type = 'master', ttl = None, extra = None):
        raise NotImplementedError()

    def create_record(self, name, zone, type, data, extra = None):
        raise NotImplementedError()

    def delete_zone(self, zone):
        raise NotImplementedError()

    def delete_record(self, record):
        raise NotImplementedError()


set_driver('dnsmadeeasy', __name__, DNSMadeEasyDNSDriver.__name__)
