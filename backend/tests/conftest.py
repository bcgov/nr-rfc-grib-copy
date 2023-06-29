import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import logging
import sys

LOGGER = logging.getLogger(__name__)

pytest_plugins = ["fixtures.fixtures_db",
                  "fixtures.fixtures_api"]

testSession = None
