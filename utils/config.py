import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ------------

import utils.logConf

# -------------

import configparser
CONFIG_FILE_PATH = './config.ini'


class configInit():
  def __init__(self):
    config_ini = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE_PATH):
      logger.error('設定ファイルがありません')
      exit(-1)
    config_ini.read(CONFIG_FILE_PATH, encoding='utf-8')
    logging.info('----設定開始----')
    try:
      self.DEBUG = config_ini['Default']['DEBUG']
      if self.DEBUG:
        self.DEBUG = True
      else:
        self.DEBUG = False
      
      self.MicID = int(config_ini['Microphone']['ID'])
      self.SamplingRate = int(config_ini['Microphone']['SamplingRate'])

      self.WavefilePath = config_ini['Wavefile']['Path']
      self.WavefileSavePath = config_ini['Wavefile']['SavePath']

    except Exception as e:
      logger.info(e)

  
  def setLogger(self, name):
    loggerTemp = logging.getLogger(name)
    if self.DEBUG:
      loggerTemp.setLevel(logging.DEBUG)
    else:
      loggerTemp.setLevel(logging.INFO)
    return loggerTemp