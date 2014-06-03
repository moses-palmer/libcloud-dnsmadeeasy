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

import json
import re
import requests

from libcloud.common.types import LibcloudError
from libcloud.dns.base import DNSDriver, Record, Zone
from libcloud.dns.providers import set_driver
from libcloud.dns.types import RecordType, ZoneAlreadyExistsError, \
    ZoneDoesNotExistError, RecordAlreadyExistsError, RecordDoesNotExistError

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

    def _to_full_record_name(self, domain, name = None):
        """Converts a domain name and record name to a full record name.

        If ``name`` is empty, it is considered to be the root record for the
        domain, and ``domain`` is returned, otherwise ``name.domain``´is
        returned.

        :param str domain: The domain name.

        :param name: The record name.
        :type name: str or None

        :return the full record name
        :rtype: str
        """
        if name:
            return '%s.%s' % (name, domain)
        else:
            return domain

    def _to_partial_record_name(self, name):
        """Converts a record name to a partial record name.

        If ``name`` is empty, it is considered to be the root record for the
        domain, and ``None`` is returned for consistency with other drivers.

        :param name: The record name.
        :type name: str or None

        :return the record name
        :rtype: str or None
        """
        # Map root names to None to be consistent with other drivers
        if not name:
            return None
        else:
            return name

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

    def _to_record(self, item, zone):
        """Converts a DNSMadeEasy record response item to a ``Record`` instance.

        :param dict item: The response item.

        :param libcloud.dns.base.Zone zone: The zone to which the record
            belongs.

        :return: a record
        :rtype: libcloud.dns.base.Record
        """
        extra = {key: value
            for key, value in item.items()
            if not key in ('id', 'name', 'type', 'value')}
        extra['fqdn'] = self._to_full_record_name(zone.domain, item['name'])

        return Record(
            id = str(item['id']),
            name = self._to_partial_record_name(item['name']),
            type = item['type'].upper(),
            data = item['value'],
            zone = zone,
            driver = self,
            extra = extra)

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
        r = self._api.dns.managed(zone.id).records.GET()
        self._raise_for_response(r)

        items = r.json()['data']
        return [self._to_record(item, zone)
            for item in items]

    def get_zone(self, zone_id):
        r = self._api.dns.managed(zone_id).GET()
        try:
            self._raise_for_response(r)
            return self._to_zone(r.json())

        except requests.exceptions.HTTPError as e:
            if r.status_code == 404:
                raise ZoneDoesNotExistError(
                    value = '', driver = self, zone_id = zone_id)
            else:
                raise

    def get_record(self, zone_id, record_id):
        # Get the Zone; this will raise ZoneDoesNotExistError if zone_id is
        # invalid
        zone = self.get_zone(zone_id)

        r = self._api.dns.managed(zone.id).records.GET()
        self._raise_for_response(r)

        items = r.json()['data']
        try:
            return next(self._to_record(item, zone)
                for item in items
                if str(item['id']) == record_id)

        except StopIteration:
            raise RecordDoesNotExistError(
                value = '', driver = self, record_id = record_id)

    def create_zone(self, domain, type = 'master', ttl = None, extra = None):
        r = self._api.dns.managed.POST(
            data = json.dumps({
                'names': [domain]}),
            headers = {
                'Content-Type': 'application/json'})

        try:
            self._raise_for_response(r)
            return self._to_zone(r.json())

        except self.ParsedError as e:
            code, message = e.args
            if code == 1 or code == 2:
                raise ZoneAlreadyExistsError(value = domain, driver = self,
                    zone_id = -1)
            else:
                raise

    def create_record(self, name, zone, type, data, extra = None):
        record = {
            'name': name,
            'type': type,
            'value': data}
        record.update(extra or {})

        r = self._api.dns.managed(zone.id).records.POST(
            data = json.dumps(record),
            headers = {
                'Content-Type': 'application/json'})
        try:
            self._raise_for_response(r)
            return self._to_record(r.json(), zone)

        except LibcloudError as e:
            # There is unfortunately currently no way other that checking the
            # error message to know whether the record already exits
            if any('exists' in error for error in e.value):
                raise RecordAlreadyExistsError(value = name, driver = self,
                    record_id = -1)
            else:
                raise

    def delete_zone(self, zone):
        r = self._api.dns.managed(zone.id).DELETE()

        try:
            self._raise_for_response(r)

        except requests.exceptions.HTTPError as e:
            if r.status_code == 404:
                raise ZoneDoesNotExistError(
                    value = zone, driver = self, zone_id = zone.id)
            else:
                raise

    def delete_record(self, record):
        raise NotImplementedError()


set_driver('dnsmadeeasy', __name__, DNSMadeEasyDNSDriver.__name__)
