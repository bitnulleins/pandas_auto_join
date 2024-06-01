import logging
import sys

setting = dict(
    JOIN_PREFIX = 'joinkey_',
    DEBUG = False,
    LOG_CONFIG = logging.basicConfig(
        level=logging.INFO,
        format = "[%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    ),
)