import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.logConf import logging
logger = logging.getLogger(__name__)

logger.info("メッセージです。")
logger.error("エラーです。")

"""
2020-01-15 16:38:53,265 __main__     INFO     メッセージです。
2020-01-15 16:38:53,266 __main__     ERROR    エラーです。
"""