import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# ------------

from utils.config import configInit
Conf = configInit()
logger = Conf.setLogger(__name__)

# ------------

import pyaudio
import wave
import scipy
import struct


class MicrophoneInput():
  def __init__(self):
    self.pAudio = pyaudio.PyAudio()

    self.setMicrophoneInfo(Conf.MicID)
    self.samplingRate = Conf.SamplingRate
    

  def getMicrophoneInfo(self):
    for i in range(self.pAudio.get_device_count()):
      tempDic = self.pAudio.get_device_info_by_index(i)
      text = 'Index: {0} | Name: {1} | ChannelNum: in {2} out {3} | SampleRate: {4}'.format(tempDic['index'], tempDic['name'], tempDic['maxInputChannels'], tempDic['maxOutputChannels'], tempDic['defaultSampleRate'])
      logger.info(text)

  def setMicrophoneInfo(self, micId = 0):
    micInfoDic = {}
    for i in range(self.pAudio.get_device_count()):
      micInfoDic = self.pAudio.get_device_info_by_index(i)
      if micInfoDic['index'] == micId:
        self.micName = micInfoDic['name']
        self.micChannelNum = micInfoDic['maxInputChannels']
        self.micSamplingRate = int(micInfoDic['defaultSampleRate'])
        text = 'Set Microphone Info || Index: {0} | Name: {1} | ChannelNum: {2} | SampleRate: {3}'.format(micId, self.micName, self.micChannelNum, self.micSamplingRate)
        logger.info(text)

        break

      if self.pAudio.get_device_count() == i + 1:
        logger.critical("対応するidのマイクロホンがありません。")

class WaveProcessing():
  def __init__(self):
    self.pAudio = pyaudio.PyAudio()

  def getWaveInfo(self):
    if not os.path.exists(Conf.WavefilePath):
      logger.critical("{0} は存在しません".format(Conf.WavefilePath))
      exit(-1)

    with wave.open(Conf.WavefilePath, 'r') as waveData:
      self.wavChannelNum = waveData.getnchannels()
      self.wavWidth = waveData.getsampwidth()
      self.wavSamplingRate = waveData.getframerate()
      self.wavFrameNum = waveData.getnframes()

      logger.info("Name {0} | ChannelNum {1} | Width {2} | SamplingRate {3} | FrameNum {4} | TotalTime {5}".format(Conf.WavefilePath, self.wavChannelNum, self.wavWidth, self.wavSamplingRate, self.wavFrameNum, 1. * self.wavFrameNum/self.wavSamplingRate))

      self.data = waveData.readframes(self.wavFrameNum)

      waveData.close()

      self.data = scipy.fromstring(self.data, dtype=scipy.int16)
      
      self.data = self.convPa2np()

      logger.debug("Numpy ver wave data: {0}".format(self.data.shape))

  def convPa2np(self):
    """
    [0, 1, 2, 3, 4, 5] 
    =>.reshape([2,3]) 
    [[0,1,2],[3,4,5]]
    =>.reshape([フレーム数, チャンネル数]).T （転置 または、order オプションを使用する）
    """
    return self.data.reshape([self.wavFrameNum, self.wavChannelNum]).T

  def convNp2pa(self):
    """
    b (チャンネル数 x フレーム数)
    array([[0, 3],
          [1, 4],
          [2, 5]])
    >>> b.reshape([-1])
    array([0, 3, 1, 4, 2, 5])
    >>> b.T.reshape([-1])
    array([0, 1, 2, 3, 4, 5])
    """
    return self.data.T.reshape([-1])
  
  def Save(self):
    logger.info("Start save as {0}".format(Conf.WavefileSavePath))
    saveData = self.convNp2pa()
    saveData = struct.pack('h' * len(saveData), *saveData)

    with wave.open(Conf.WavefileSavePath, 'w') as ww:
      ww.setnchannels(self.wavChannelNum)
      ww.setsampwidth(self.wavWidth)
      ww.setframerate(self.wavSamplingRate)
      ww.writeframes(saveData)
      logger.info("End Save as {0}".format(Conf.WavefileSavePath)) 
  
  def getData(self, data, samplingRate = None):
    #channel num x frame num
    self.data = data
    self.wavChannelNum, self.wavFrameNum = self.data.shape
    if samplingRate is not None:
      self.wavSamplingRate = samplingRate

if __name__ == '__main__':
  mI= MicrophoneInput()
  mI.getMicrophoneInfo()
  
  wP = WaveProcessing()
  wP.getWaveInfo()
  wP.getData(wP.data)
  wP.Save()
  