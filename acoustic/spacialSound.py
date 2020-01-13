import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# ------------

from utils.config import configInit
Conf = configInit()
logger = Conf.setLogger(__name__)

from acoustic.acousticSignalProc import SpectrogramProcessing
spec = SpectrogramProcessing()
# -------------


import re
import pickle
import numpy as np
import math

"""
        Head F
          x
          ^
Left　<-- z  Right

http://www.sp.m.is.nagoya-u.ac.jp/HRTF/
HRTF data (2)

中部TLO
E-mail: ctlo@nisri.jp
ID Number: NU-0234 (頭部音響伝達関数データベース)
西野隆典, 梶田将司, 武田一哉, 板倉文忠, "水平方向及び仰角方向に関 する頭部伝達関数の補間," 日本音響学会誌, 57巻, 11号, pp.685-692, 2001.
"""
class HRTF():
  def __init__(self):
    super().__init__()
    self.elev = [] #[-40, -30, ,,,]
    self.azimuth = [] #[[0, 5, ..], [...]]
    self.Lpath = []
    self.Rpath = []
    self.hrtf = [[],[]]
    self.left = 0
    self.right = 1
  
  def checkModel(self):
    if os.path.isdir(Conf.HRTFmodel):
      logger.info("{0} からHRTFを読み込む".format(Conf.HRTFmodel))
      self.getModelNameList()
    else:
      logger.critical("HRTFの音響情報のパスがない")
      exit(-1)

  def getModelNameList(self):
    dirList = os.listdir(path=Conf.HRTFmodel)
    dirList = sorted(dirList)
    
    
    for dirName in dirList:
      if len(dirName) > 4:
        if dirName[:4] == 'elev':
          self.elev.append(int(dirName[4:]))
          dir = os.path.join(Conf.HRTFmodel, dirName)

          fileList = os.listdir(path=dir)
          fileList = sorted(fileList)
          azimuth = []
          Lpath = []
          Rpath = []
          for fileN in fileList:
            path = os.path.join(dir, fileN)
            fileN, ext = os.path.splitext(fileN)
           
          
            if ext == ".dat":
              if fileN[0] == "L":
                ele = int(re.findall('L(.*)e', fileN)[0])
                azi = int(re.findall('e(.*)a', fileN)[0])
                azimuth.append(azi)
                Lpath.append(path)
              elif fileN[0] == "R":
                Rpath.append(path)
          
          self.azimuth.append(azimuth)
          self.Lpath.append(Lpath)
          self.Rpath.append(Rpath)
    
    sorted_ind = [*range(len(self.elev))]
    sorted_ind = sorted(sorted_ind, key=lambda i: self.elev[i])
    self.elev = [self.elev[i] for i in sorted_ind]
    self.azimuth = [self.azimuth[i] for i in sorted_ind]
   
    self.Lpath = [self.Lpath[i] for i in sorted_ind]
    self.Rpath = [self.Rpath[i] for i in sorted_ind]
  
  def openData(self, path, dataType = np.int16):
    with open(path, 'r') as rData:
      #data = np.fromstring(data.read(), dtype=dataType)

      #data = data.astype(np.float32)/np.iinfo(np.int16).max
      #data = data.read()
      
      temp = rData.read().split("\n")
      data = []
      for item in temp:
        if item != '':
          data.append(float(item))
      return np.array(data)
  
  def convHRTF2Np(self):
    for e, _ in enumerate(self.elev):
      LaziData = []
      RaziData = []
      for a, _ in enumerate(self.azimuth[e]):
        
        Lpath = self.Lpath[e][a]
        Rpath  = self.Rpath[e][a]

        #data = spec.fft(self.openData(Lpath))
        #Ldata = spec.fftNoWindow(self.openData(Lpath))
        #Rdata = spec.fftNoWindow(self.openData(Rpath))
        #Ldata = spec.fft(self.openData(Lpath))
        #Rdata = spec.fft(self.openData(Rpath))
        Ldata = spec.overlapAdderFFT(self.openData(Lpath))
        Rdata = spec.overlapAdderFFT(self.openData(Rpath))
        
        LaziData.append(Ldata)
        RaziData.append(Rdata)

      self.hrtf[self.left].append(LaziData)
      self.hrtf[self.right].append(RaziData)

    self.saveData(self.hrtf, Conf.HRTFpath)
    self.saveData(self.elev, Conf.Elevpath)
    self.saveData(self.azimuth, Conf.Azimuthpath)
    logger.info("Success save HRTF data")

  def saveData(self, data, path):
    try:
      with open(path, 'wb') as hrtf:
        pickle.dump(data, hrtf)
    except Exception as e:
      logger.critical(e)

  def readData(self, path):
    #read data
    # [left0 or right1][ele][azi]
    #
    try:
      with open(path, 'rb') as hrtf:
        data = pickle.load(hrtf)
    except Exception as e:
      logger.critical(e)

    return data
        
  

class spacialSound():
  def __init__(self):
    self.dataInit()
    self.StdSoundDis = 1.
    self.SoundDisMin = 0.2
  
  def dataInit(self):
    self.hrtf = HRTF()
    self.hrtfFreq = self.hrtf.readData(Conf.HRTFpath)
    self.elev = self.hrtf.readData(Conf.Elevpath)
    self.azimuth = self.hrtf.readData(Conf.Azimuthpath)
    self.StdDist = 1.4 #[m]

    self.npElev = np.array(self.elev)
    self.npAzi = []
    for aziList in self.azimuth:
      self.npAzi.append(np.array(aziList))

    

  def pos2spherialCoordinate(self, x, y, z):
    #x, y, z [m]
    if y >= 0:
      sgn = 1
    elif y < 0:
      sgn = -1
    try:
      azi = sgn * math.acos(x / math.sqrt(x ** 2 + y ** 2))
      if azi < 0:
        azi = np.pi - azi
    except ZeroDivisionError as e:
      azi = 0
    elev = math.asin(z / math.sqrt(x ** 2 + y ** 2 + z ** 2))
    
    return  elev * 180/np.pi, azi * 180/np.pi
  
  def disanceAtenuation(self, data, x, y, z):
    dis = math.sqrt(x ** 2 + y ** 2 + z ** 2)
    if self.SoundDisMin > dis:
      return data/dis
    else:
      return data/self.SoundDisMin

  def getNearestDegIdx(self, elev, azi):
    #logger.debug("Input position deg: azi : {0}, elev : {1}".format(azi, elev))
    
    eleIdx = np.abs(self.npElev - elev).argmin()
    
    aziIdx = np.abs(self.npAzi[eleIdx] - azi).argmin()
    return eleIdx, aziIdx

  def getHRTF(self, x, y, z):
    ele, azi = self.pos2spherialCoordinate(x, y, z)
    eId, aId = self.getNearestDegIdx(ele, azi)
    Lhrtf = self.hrtfFreq[0][eId][aId]
    Rhrtf = self.hrtfFreq[1][eId][aId]
    return Lhrtf, Rhrtf

if __name__ == '__main__':
  
  hrtf = HRTF()
  hrtf.checkModel()
  hrtf.openData(hrtf.Lpath[0][0])
  hrtf.convHRTF2Np()
  """
  spec = spacialSound()
  ele, azi = spec.pos2spherialCoordinate(-1,-1,1)
  eId, aId = spec.getNearestDegIdx(ele, azi)

  print(ele, eId)
  print(azi, aId)
  """