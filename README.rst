Driver for DNSMadeEasy for Apache libcloud
==========================================

This package allows you to use `DNSMadeEasy <http://www.dnsmadeeasy.com/>`_ with
`Apache libcloud <https://libcloud.apache.org/>`_.

To use it, simply import the ``dnsmadeeasy`` module and create the driver
instance:

.. code-block::

    import libcloud.dns.providers
    import dnsmadeeasy

    API_KEY = '...'
    API_SECRET = '...'

    Driver = libcloud.dns.providers.get_driver('dnsmadeeasy')
    connection = Driver(API_KEY, API_SECRET)
