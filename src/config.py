import logging
import sys
import uuid

# Simple config dict
setting = dict(
    UUID = uuid.uuid4().hex,
    DEBUG = False,
    LOG_CONFIG = logging.basicConfig(
        level=logging.INFO,
        format = "[%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    ),
)