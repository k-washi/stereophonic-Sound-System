import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# ------------

from utils.config import configInit
Conf = configInit()

from utils.logConf import logging
logger = logging.getLogger(__name__)
# -----------

logger.info(Conf.MicID)