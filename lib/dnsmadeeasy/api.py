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

import collections
import hammock
import hashlib
import hmac
import time


class Headers(collections.Mapping):
    def __init__(self, api_key, api_secret, *args, **kwargs):
        """A mapping that returns calculated values when :func:`items` is
        called.

        The values calculated are consistent each time :func:`items` is called.

        :param str api_key: The API key.

        :param str api_secret: The API secret.
        """
        super(Headers, self).__init__(*args, **kwargs)
        self._api_key = api_key
        self._secret = api_secret.encode()

    def get_time(self):
        """Returns the timestamp for now.

        The timestamp is in the format required by DNSMadeEasy.

        :return: a timestamp
        :rtype: time.time
        """
        return time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())

    def get_hash(self, t):
        """Returns the hash of a timestamp.

        The hash is mixed with the API secret.

        :param str t: The timestamp to hash.

        :return: a hex digest
        :rtype: str
        """
        return hmac.new(
            self._secret,
            t.encode(),
            hashlib.sha1).hexdigest()

    def __getitem__(self, key):
        raise NotImplementedError()

    def __iter__(self):
        raise NotImplementedError()

    def __len__(self):
        raise NotImplementedError()

    def items(self):
        """Returns the headers expected by DNSMadeEasy for authentication.

        The values are calculated when this method is called, so the timestamps
        and hashes are consistent.

        :return: the headers expected by DNSMadeEasy
        """
        t = self.get_time()
        h = self.get_hash(t)
        return (
            ('x-dnsme-apiKey', self._api_key),
            ('x-dnsme-hmac', h),
            ('x-dnsme-requestDate', t))


class DNSMadeEasyAPI(hammock.Hammock):
    ENTRY_POINT_LIVE = 'https://api.dnsmadeeasy.com/V2.0'
    ENTRY_POINT_SANDBOX = 'https://sandbox.dnsmadeeasy.com'

    def __init__(self, api_key, api_secret, sandbox = False):
        """Creates a DNSMadeEasyAPI instance.

        This object works just like a :class:`~hammock.Hammock` instance, but
        also sets the correct request headers based on ``api_key`` and
        ``api_secret``.

        :param str api_key: The DNSMadeEasy API key.

        :param str api_secret: The DNSMadeEasy secret.
        """
        super(DNSMadeEasyAPI, self).__init__(
            self.ENTRY_POINT_SANDBOX if sandbox else self.ENTRY_POINT_LIVE,
            headers = Headers(api_key, api_secret),
            verify = not sandbox)
