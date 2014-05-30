from .. import *

import os
import re

# Create the regular expression to find test modules
extension = '.py'
pattern = re.compile(
    r'[^_].*?'
    + re.escape(extension) + '$')

# Define __all__ to make "from tests.suites import *" work
__all__ = [f[:-len(extension)]
    for f in os.listdir(__path__[0])
    if pattern.match(f)]
