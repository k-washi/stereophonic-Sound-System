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
import numpy as np
import struct



class AudioDevice():
  def __init__(self, devId = Conf.MicID):
    self.pAudio = pyaudio.PyAudio()

    self.setAudioDeviceInfo(devId)
    self.samplingRate = Conf.SamplingRate
    

  def getAudioDeviceInfo(self):
    for i in range(self.pAudio.get_device_count()):
      tempDic = self.pAudio.get_device_info_by_index(i)
      text = 'Index: {0} | Name: {1} | ChannelNum: in {2} out {3} | SampleRate: {4}'.format(tempDic['index'], tempDic['name'], tempDic['maxInputChannels'], tempDic['maxOutputChannels'], tempDic['defaultSampleRate'])
      logger.info(text)

  def setAudioDeviceInfo(self, micId = 0):
    micInfoDic = {}
    for i in range(self.pAudio.get_device_count()):
      micInfoDic = self.pAudio.get_device_info_by_index(i)
      if micInfoDic['index'] == micId:
        self.micName = micInfoDic['name']
        self.micChannelNum = micInfoDic['maxInputChannels']
        self.micOutChannelNum = micInfoDic['maxOutputChannels'] 
        self.micSamplingRate = int(micInfoDic['defaultSampleRate'])
        text = 'Set Audio Device Info || Index: {0} | Name: {1} | ChannelNum: {2}, {3} | SampleRate: {4}'.format(micId, self.micName, self.micChannelNum,self.micOutChannelNum, self.micSamplingRate)
        logger.info(text)

        if self.micChannelNum > 2:
          logger.critical("3個以上のマイクロホン入力に対応していません。")
          exit(-1)

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

      self.pAdata = waveData
      self.data = waveData.readframes(self.wavFrameNum)

      waveData.close()
      
      if self.wavWidth == 2:
        self.data = scipy.fromstring(self.data, dtype=scipy.int16)
      elif self.wavWidth == 4:
        self.data = scipy.fromstring(self.data, dtype=scipy.int32)
      else:
        logger.critical("ハイレゾ音源などの対応していないデータ形式です。")
        exit(-1)
      
      self.data = convPa2np(self.data, self.wavChannelNum)

      logger.debug("Numpy ver wave data: {0}".format(self.data.shape))


  
  def Save(self):
    logger.info("Start save as {0}".format(Conf.WavefileSavePath))
    saveData = convNp2pa(self.data)
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


# -------- Utils -----------------

def convPa2np(data,channelNum):
  """
  [0, 1, 2, 3, 4, 5] 
  =>.reshape([2,3]) 
  [[0,1,2],[3,4,5]]
  =>.reshape([フレーム数, チャンネル数]).T （転置 または、order オプションを使用する）
  """
  return data.reshape([-1, channelNum]).T

def convNp2pa(data):
  """
  b (チャンネル数 x フレーム数)
  array([[0, 3],
        [1, 4],
        [2, 5]])＝
  >>> b.reshape([-1])
  array([0, 3, 1, 4, 2, 5])
  >>> b.T.reshape([-1])
  array([0, 1, 2, 3, 4, 5])
  """
  return data.T.reshape([-1]) 


class SpectrogramProcessing():
  def __init__(self, freq = Conf.SamplingRate):
    self.window = np.hamming(Conf.SysChunk)
    self.freq = np.fft.rfftfreq(Conf.SysChunk, d=1./freq)
   
  def fft(self, data):
    #in data: chanel_num x frame num(Conf.SysChunk)
    #out: chanel_num x freq num (if 1.6kHz, 0,...,7984.375 Hz) 
    data = np.fft.rfft(data * self.window)
   
    return data

  def ifft(self, data):
    #in: chanel_num x freq num (if 1.6kHz, 0,...,7984.375 Hz) 
    #out: chanel_num x frame num(Conf.SysChunk)
    data = np.fft.irfft(data)
    return data


if __name__ == '__main__':
  mI= AudioDevice()
  mI.getAudioDeviceInfo()
  
  wP = WaveProcessing()
  wP.getWaveInfo()
  wP.getData(wP.data)
  wP.Save()
  