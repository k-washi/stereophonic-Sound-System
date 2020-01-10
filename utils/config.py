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
      self.DEBUG = bool(config_ini['Default']['DEBUG'])

      self.MicID = int(config_ini['Microphone']['ID'])
      self.SamplingRate = int(config_ini['Microphone']['SamplingRate'])

      self.OutpuID = int(config_ini['Output']['ID'])
      self.Record = bool(int(config_ini['Output']['Record']))
      self.RecordTime = float(config_ini['Output']['RecordTime'])

      self.WavefilePath = config_ini['Wavefile']['Path']
      self.WavefileSavePath = config_ini['Wavefile']['SavePath']

      self.SysChunk = int(config_ini['System']['Chunk'])
      self.SysFFToverlap = int(config_ini['System']['FFToverlap'])
      self.SysSampleWidth = int(config_ini['System']['SampleWidth'])
      self.SysCutTime = float(config_ini['System']['CutTime'])

    except Exception as e:
      logger.info(e)

  
  def setLogger(self, name):
    loggerTemp = logging.getLogger(name)
    if self.DEBUG:
      loggerTemp.setLevel(logging.DEBUG)
    else:
      loggerTemp.setLevel(logging.INFO)
    return loggerTemp