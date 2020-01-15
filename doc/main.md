# Pythonで始める音響信号処理　- 立体音響システムを作ろう

# 概要

昨今、VTuberなど3Dモデルを用いた配信者が増えてきている。多くの配信者はモノチャネルの音響情報を用いて配信しているが、より没入感のある配信を行うため、3Dioなどのマイクロホンアレイを用いることで、立体音響を生成している。複数の音源がある場合、このようなマイクロホンアレイを用いることをおすすめするが、例えばASMRなどのシチュエーションにおいて、単一音源(人物)を立体音響にする場合、信号処理により立体音響を生成できる。もちろん、複数音源でも可能であるが、、、

ここで重要になるのが、頭部伝達関数である、3DioなどASMRに使用されるマイクロホンアレイのマイク部分は耳の形をしている。これは、音源から、耳の鼓膜までの音の伝達を模倣している。この伝達を頭部伝達関数(HRTF)と呼ぶ。
本記事では、この右, 左耳までのHRTFを用いた信号処理で立体音響を生成するシステムをPythonで実装する方法を記載する。

注意点: HRTFは個人差があり、前後の音像位置推定が不一致になることが多々あります。実際、3Dio等を使用した場合も、標準的な耳の形を模倣しただけであり、個人差を解決できていません。

プログラムが長いため概要のみ説明していきます。詳細は以下のGitのプログラムを読んでみてください。
また、使用方法に関しても、gitに記載しています。
Git: [k-washi/stereophonic-Sound-System](https://github.com/k-washi/stereophonic-Sound-System)

また、loggingや設定ファイルの読み込み、位置情報取得のためのgRPC通信に関しては、以下のQiitaの記事を適宜参考にしてください。

+ [Pythonで始めるgRPC](https://qiita.com/kwashi/items/8e5fb365874f1f88cdaa)
+ [python configparser によるパラメータ設定](https://qiita.com/kwashi/items/3a6df37978d811b48cfa)
+ [Pythonのloggingモジュールの使い方](https://qiita.com/kwashi/items/576c5b287dfc08d404f3)


# 立体音響例 (イヤホン必須です)

以下の画像をクリックしてみてください。
Youtubeのリンクで実際に作成した立体音響が聞けます。マイクがmac付属のもののため、もともとの音が悪いですが、立体音響になっていることはわかると思います。

[![IMAGE ALT TEXT HERE](http://img.youtube.com/vi/YOUTUBE_VIDEO_ID_HERE/0.jpg)](http://www.youtube.com/watch?v=jlyv53obQPY)

# ライブラリのインストール

```bash

pip install PyAudio==0.2.11
pip install grpcio-tools
pip install numpy
```

# HRTFの取得

ここでは、HRTFのデータベースを読み込み周波数情報に変換しNumpy形式で保存する。

HRTFは、[名古屋大学 HRTF](http://www.sp.m.is.nagoya-u.ac.jp/HRTF/)のHRTF data (2)を使用した。
※　西野隆典, 梶田将司, 武田一哉, 板倉文忠, "水平方向及び仰角方向に関 する頭部伝達関数の補間," 日本音響学会誌, 57巻, 11号, pp.685-692, 2001.

以下に、プログラムを記載する。細かい部分は、...として省略している。全プログラムを見る場合は、[acoustic/spacialSound.py](https://github.com/k-washi/stereophonic-Sound-System/blob/master/acoustic/spacialSound.py)を見てください。

```python:acoustic/spacialSound.py
...

class HRTF():
  def __init__(self):
    ...
  
  def checkModel(self):
    #モデルファイル名を取得
    ...
      self.getModelNameList()
    ...

  def getModelNameList(self):
    #方位角、仰角ごとにHRTFファイル名を解析
    ...
  
  def openData(self, path, dataType = np.int16):
    #H各方向,仰角のHRTF信号のサンプル数は512点であり、このデータを読み込んでnumpy形式に変換している
    with open(path, 'r') as rData:
      temp = rData.read().split("\n")
      data = []
      for item in temp:
        if item != '':
          data.append(float(item))
      return np.array(data)
  
  def convHRTF2Np(self):
    #各方位角、仰角のHRTFデータを読み込み、overlap Adder methodに基づき 512点 + 0埋め(512点)をFFTしている。(FFTに関しては次章に記載)
    #上記のFFTを両耳に関して行い、全データをpickleで保存している。保存はsaveData関数を用いている。
    #読み込みは、保存したpickleデータは、readDataで読み込むことができる。
    for e, _ in enumerate(self.elev):
      LaziData = []
      RaziData = []
      for a, _ in enumerate(self.azimuth[e]):
        
        Lpath = self.Lpath[e][a]
        Rpath  = self.Rpath[e][a]

        Ldata = spec.overlapAdderFFT(self.openData(Lpath))
        Rdata = spec.overlapAdderFFT(self.openData(Rpath))
        
        LaziData.append(Ldata)
        RaziData.append(Rdata)

      self.hrtf[self.left].append(LaziData)
      self.hrtf[self.right].append(RaziData)

    self.saveData(self.hrtf, Conf.HRTFpath)
    self.saveData(self.elev, Conf.Elevpath)
    self.saveData(self.azimuth, Conf.Azimuthpath)

  def saveData(self, data, path):
    #pickleデータ保存
    try:
      with open(path, 'wb') as hrtf:
        pickle.dump(data, hrtf)
    except Exception as e:
      logger.critical(e)

  def readData(self, path):
    #pickleデータ読み込み
    try:
      with open(path, 'rb') as hrtf:
        data = pickle.load(hrtf)
    except Exception as e:
      logger.critical(e)

    return data
```

# 高速フーリエ変換(FFT)

ここでは、FFTに関する実装について説明する。

詳細は、[acoustic/acousticSignalProc.py](https://github.com/k-washi/stereophonic-Sound-System/blob/master/acoustic/acousticSignalProc.py)

音響情報を処理する際、HRTFとマイク入力の畳み込み積分が必要となる。しかし、生の音響信号で処理した場合に、処理に時間がかかり、かつ、データも扱いづらい。そのため、信号を周波数領域の情報に変換するフーリエ変換が必要となる。そして、このフーリエ変換を高速に行うものがFFTである。

HRTFとマイク入力を畳み込むとき、OverLap Add method (OLA)がよく用いられる。
例えば、HRTFとマイク入力のサンプル数が512点の場合、各データに加えて、512点を0埋めする。つまり512 + 512(0)のデータを作成する。
その後、numpyのrfft関数でFFTの正の周波数を計算している。
例えば、numpyのfftの場合、512/2 = 256点の正の周波数成分と256点の負の周波数成分が計算される。しかし、多くの工学的な用途では正の周波数成分のみで十分な場合が多い。
また、numpyのrfftとfftの計算アルゴリズムが異なるが結果の誤差はかなり小さいため、今回はrfftを用いている。
そして、FFTの実行後、HRTFとマイク入力を各周波数ごとに掛け合わせる。このかけわせに関しては、次の章で説明する。

以下のプログラムでは、overlapAdderFFTとspacializeFFTの２つのFFTを準備している。違いは。window(窓関数）をかけ合わせているかどうかである。
窓関数は、フーリエ変換が切り出した範囲の周期性を仮定しているため、端を小さくするような関数をデータにかけて端と端がつながるようにしている。
ただし、HRTFは、1データ512点しかなく、窓関数をかけた場合、もとのデータを復元できないため、窓関数をかけずに使用している。
一方で、マイク入力は、窓関数をかけている。
次章で説明するが、窓関数をかけた場合、端の情報がなくなるため、各データを128点づつずらしながら使用している。

```python:acoustic/acousticSignalProc.py
import pyaudio
import numpy as np


class SpectrogramProcessing():
  def __init__(self, freq = Conf.SamplingRate):
    self.window = np.hamming(Conf.SysChunk)
    self.overlapFreq = np.fft.rfftfreq(Conf.SysChunk * 2, d=1./freq)
    self.overlapData = np.zeros((int(Conf.SysChunk * 2)), dtype = np.float32)
  
  def overlapAdderFFT(self, data):
    #0埋めしてFFT
    self.overlapData[:Conf.SysChunk] = data
    return np.fft.rfft(self.overlapData)
  
  def spacializeFFT(self, data):
    #0埋めかつ、hanning windowをかける。
    self.overlapData[:Conf.SysChunk] = data * self.window
    return np.fft.rfft(self.overlapData)


  def ifft(self, data):
    #in: chanel_num x freq num (if 1.6kHz, 0,...,7984.375 Hz) 
    #out: chanel_num x frame num(Conf.SysChunk = 512)
   
    return np.fft.irfft(data)

```

# マイク入力, 出力, 音響処理プログラム

次に、実際にマイク入力、出力、そして、立体音響への変換プログラムを背逸名する。
上記で説明した関数等を用いて、処理していく。また、設定やgRPCに関しては、最初に記載した通り、私の過去記事を参考にしてください。

```python:acoustic/audioStreamOverlapAdder.py

...

from acoustic.acousticSignalProc import AudioDevice, SpectrogramProcessing, WaveProcessing, convNp2pa, convPa2np
from acoustic.spacialSound import spacialSound
# ------------

import pyaudio
import numpy as np
import time

class MicAudioStream():
  def __init__(self):
    self.pAudio = pyaudio.PyAudio()
    self.micInfo = AudioDevice(Conf.MicID)
    self.outInfo = AudioDevice(Conf.OutpuID)

    #出力デバイスの制限処理
    if self.outInfo.micOutChannelNum < 2:
      self.left = 0
      self.right = 0
    else:
      self.left = 0
      self.right = 1
      if self.outInfo.micOutChannelNum > 2:
        self.outInfo.micChannelNum = 2
        logger.info("出力マイク数が過剰であるため2チャンネルに制限しました。")

    self.startTime = time.time()

    #現在は16bitのビット幅のみ対応している。(他の場合の動作を確認できていないため)
    if Conf.SysSampleWidth == 2:
      self.format = pyaudio.paInt16
      self.dtype = np.int16
    else:
      logger.critical("現在対応していない")
      exec(-1)

    self.fft = SpectrogramProcessing()

    #毎回numpyのarray形式のデータを作成し、メモリー確保を実行した場合、時間がかかるため、予め作成しておく。
    self.data = np.zeros((int(Conf.StreamChunk * 2)), dtype=self.dtype)
    self.npData = np.zeros((int(Conf.StreamChunk * 2)) , dtype=self.dtype)

    self.overlapNum = int(Conf.StreamChunk / Conf.SysFFToverlap) 

    self.freqData = np.zeros((self.overlapNum, self.outInfo.micOutChannelNum, self.fft.overlapFreq.shape[0]), dtype=np.complex)
    self.convFreqData = np.zeros((self.outInfo.micOutChannelNum, int(Conf.StreamChunk*3)) , dtype=self.dtype)
    self.outData = np.zeros((self.outInfo.micOutChannelNum * Conf.StreamChunk), dtype=self.dtype)
    
    self.Aweight = self.fft.Aweight() #A特性をかけているが、ほとんど変わらなかったため、気にする必要はない。（消しても良い）

    #位置情報の初期値
    self.x = 0.2
    self.y = 10
    self.z  = 0.2

    #HRTFの読み込み（acoustic/spacialSound.py）
    #位置情報に対して、HRTFを返す処理を実行できる
    self.hrft = spacialSound()
    
    #立体音響を録音する場合、
    if Conf.Record:
      #test/listOrNumpy.pyにて速度比較
      # numpyのArray形式は、array形式を結合していくより、一旦、numpyをlistに変換してlistの拡張を行った方が早い
      self.recordList = []

  def spacialSoundConvering(self, freqData):
    #位置に対して、HRTFを返している
    lhrtf, rhrtf = self.hrft.getHRTF(self.x, self.y, self.z)
   
    #以下のようにHRTFのマイクの入力データを畳み込み、立体音響を生成している。
    freqData[self.left] = freqData[self.left] * lhrtf 
    freqData[self.right] = freqData[self.right] * rhrtf 
    return freqData * self.Aweight

  def callback(self, in_data, frame_count, time_info, status):
    #pyAudioのstream処理で、音データを処理する関数。
    #in_dataが入力で、returnでout_dataとして、音データを出力している。

    if time.time() - self.startTime > Conf.SysCutTime:
      #pyAudio形式の入力をnumpy形式に変換している。
      self.npData[Conf.StreamChunk:] = convPa2np(np.fromstring(in_data, self.dtype), channelNum=self.micInfo.micChannelNum)[0, :] #ch1 input
      
      #以下でデータをオーバーラップ幅(128)づつずらしながら、立体音響を生成する。
      for i in range(self.overlapNum):
        #512点(SysChunk)の幅でFFTをおこなっている。
        self.freqData[i, :, :] = self.fft.spacializeFFT(self.npData[Conf.SysFFToverlap * i : Conf.SysChunk + Conf.SysFFToverlap * i])
        
        #HRTFとマイク入力を畳み込んでいる。
        self.freqData[i, :, :] = self.spacialSoundConvering(self.freqData[i]) 
        
        #逆フーリエ変換で周波数領域から時間領域へ変換している。
        self.convFreqData[:, Conf.SysFFToverlap * i  : Conf.SysChunk * 2 + Conf.SysFFToverlap * i] += self.fft.ifft(self.freqData[i]).real.astype(self.dtype)#[:,:Conf.SysChunk]

      #numpy形式からpyAudioで出力する形式に変換している。
      self.outData[:] = convNp2pa(self.convFreqData[:,:Conf.StreamChunk]) 

      #音の距離減衰を計算している。また、音が大きすぎるので、SysAttenuationで割っている。
      self.outData[:] = self.hrft.disanceAtenuation(self.outData[:], self.x, self.y, self.z) / Conf.SysAttenuation
      
      if Conf.Record:
        self.recordList += self.outData.tolist()
      
      #次のマイク入力に備えて初期化
      self.npData[:Conf.StreamChunk] = self.npData[Conf.StreamChunk:]
      self.convFreqData[:, :Conf.StreamChunk*2] = self.convFreqData[:, Conf.StreamChunk:]
      self.convFreqData[:,Conf.StreamChunk*2:] = 0
      
    #pyAudio形式であるデータを出力する形式に変換
    out_data = self.outData.tostring()
    
    return (out_data, pyaudio.paContinue)
  

  
  def start(self):
    #以下の形式で、入出力のデバイスや形式を設定し、処理を開始する。
    """
    rate – Sampling rate
    channels – Number of channels
    format – Sampling size and format. See PortAudio Sample Format.
    input – Specifies whether this is an input stream. Defaults to False.
    output – Specifies whether this is an output stream. Defaults to False.
    input_device_index – Index of Input Device to use. Unspecified (or None) uses default device. Ignored if input is False.
    output_device_index – Index of Output Device to use. Unspecified (or None) uses the default device. Ignored if output is False.
    frames_per_buffer – Specifies the number of frames per buffer.
    start – Start the stream running immediately. Defaults to True. In general, there is no reason to set this to False.
    input_host_api_specific_stream_info – Specifies a host API specific stream information data structure for input.
    output_host_api_specific_stream_info – Specifies a host API specific stream information data structure for output.
    stream_callback –Specifies a callback function for non-blocking (callback) operation. Default is None, which indicates blocking operation (i.e., Stream.read() and Stream.write()). To use non-blocking operation, specify a callback that conforms to the following signature:
    callback(in_data,      # recorded data if input=True; else None
            frame_count,  # number of frames
            time_info,    # dictionary
            status_flags) # PaCallbackFlags
    time_info is a dictionary with the following keys: input_buffer_adc_time, current_time, and output_buffer_dac_time; see the PortAudio documentation for their meanings. status_flags is one of PortAutio Callback Flag.
    The callback must return a tuple:
    (out_data, flag)
    out_data is a byte array whose length should be the (frame_count * channels * bytes-per-channel) if output=True or None if output=False. flag must be either paContinue, paComplete or paAbort (one of PortAudio Callback Return Code). When output=True and out_data does not contain at least frame_count frames, paComplete is assumed for flag.
    """
    self.stream = self.pAudio.open(
      format = self.format,
      rate = Conf.SamplingRate,#self.micInfo.samplingRate,
      channels = self.micInfo.micChannelNum,
      input = True,
      output = True,
      input_device_index = Conf.MicID,
      output_device_index = Conf.OutpuID,
      stream_callback = self.callback,
      frames_per_buffer = Conf.StreamChunk
    )

    self.stream.start_stream()

  def stop(self):
    #音響処理とは別に必要な処理を実行している。また、最終的に、システムの終了を実行する際のクローズ処理も実行している。
    #ここでは、gRPCを使用して、音源位置の情報を更新している。

    from proto.client import posClient
    
    grpcPosGetter = posClient()
    grpcPosGetter.open()

    while self.stream.is_active():
      time.sleep(0.1)
      try:
        ok = grpcPosGetter.posRequest()
        if ok:
          self.x, self.y, self.z = grpcPosGetter.getPos()
      except Exception as e:
        logger.error("pos getter error {0}".format(e))

      if time.time() - self.startTime > Conf.RecordTime + Conf.SysCutTime:
        break

    if Conf.Record:
      record = WaveProcessing()
      record.SaveFlatteData(self.recordList, channelNum=self.outInfo.micOutChannelNum)


    self.stream.start_stream()
    self.stream.close()
    self.close()
    grpcPosGetter.close()
    

  
  def close(self):
    self.pAudio.terminate()
    logger.debug("Close proc")
    exit(0)

if __name__ == "__main__":
  st = MicAudioStream()
  st.start()
  try:
    pass
  finally:
    st.stop()
  

```

# 入力、出力デバイスの確認

実際に音響処理を試すためには、入出力デバイスのIDを確認する必要がある。

デバイス情報例

```bash
2020-01-16 03:46:49,436 [acousticSignalProc.py:34] INFO     Index: 0 | Name: Built-in Microphone | ChannelNum: in 2 out 0 | SampleRate: 44100.0
2020-01-16 03:46:49,436 [acousticSignalProc.py:34] INFO     Index: 1 | Name: Built-in Output | ChannelNum: in 0 out 2 | SampleRate: 44100.0
2020-01-16 03:46:49,436 [acousticSignalProc.py:34] INFO     Index: 2 | Name: DisplayPort | ChannelNum: in 0 out 2 | SampleRate: 48000.0
...
```

以下に、PyAudioを用いて入出力デバイスの情報を出力するプログラムを示す。

```python:acoustic/acousticSignalProc.py
...

import pyaudio
import numpy as np

class AudioDevice():
  def __init__(self, devId = Conf.MicID):
    self.pAudio = pyaudio.PyAudio()

    self.setAudioDeviceInfo(devId)
    self.samplingRate = Conf.SamplingRate
    

  def getAudioDeviceInfo(self):
    #PyAudioを用いてデバイス情報を出力する。
    for i in range(self.pAudio.get_device_count()):
      tempDic = self.pAudio.get_device_info_by_index(i)
      text = 'Index: {0} | Name: {1} | ChannelNum: in {2} out {3} | SampleRate: {4}'.format(tempDic['index'], tempDic['name'], tempDic['maxInputChannels'], tempDic['maxOutputChannels'], tempDic['defaultSampleRate'])
      logger.info(text)

  def setAudioDeviceInfo(self, micId = 0):
    #設定したデバイスIDが存在するか確認し、そのIDの情報を保持する
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
```

# まとめ

以上、Pythonを用いた立体音響システムに関する解説でした。
かなり省いた部分もあり、また、他の記事も参考にする必要があるため、複雑になっているかもしれませんが、参考になればと思います。
pythonは遅いと言われていますが、予めメモリを確保しておくなどし、numpyを効率的に使っていけば、十分な速度で実行可能なことが多いです。
他にも、いろいろ記事を書いているので参考にしてみてください。