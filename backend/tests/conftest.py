import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import logging
import sys

LOGGER = logging.getLogger(__name__)

pytest_plugins = ["fixtures_db"]

testSession = None
