from .. import *

import os
import re
import sys

# Create the regular expression to find test modules
extension = '.py'
pattern = re.compile(
    r'[^_].*?'
    + re.escape(extension) + '$')

# Define __all__ to make "from tests.suites import *" work
__all__ = [f[:-len(extension)]
    for f in os.listdir(__path__[0])
    if pattern.match(f)]

RESOURCE_DIR = os.path.join(
    os.path.dirname(__file__),
    os.path.pardir,
    'resources')
try:
    with open(os.path.join(RESOURCE_DIR, 'api-information')) as api_file:
        API_KEY, API_SECRET = iter(l.strip()
            for l in api_file
            if l.strip())
except IOError:
    printf(r'''
The file %s does not exist. It must be on the following format:
API_KEY
API_SECRET

Empty lines are ignored.''' % (
            os.path.relpath(os.path.join(RESOURCE_DIR, 'api-information'))))
    sys.exit(1)
except ValueError:
    printf(r'''
The file %s is invalid. It must be on the following format:
API_KEY
API_SECRET

Empty lines are ignored.''' % (
            os.path.relpath(os.path.join(RESOURCE_DIR, 'api-information'))))
    sys.exit(1)
