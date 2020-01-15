# python configparser による設定

pythonの標準ライブラリーであるconfigparserを用いた設定方法と、設定パラメータの使用方法に関して記載しています。

git : [k-washi](https://github.com/k-washi/stereophonic-Sound-System/blob/master/utils/config.py)

# Iniファイル

configparserで読み込む設定を記載するファイルです。
例としては、以下のように記載できます。
コメントは#を使用して書くことができます。

```ini:config.ini
[Microphone]
#マイクのID
ID = 0
SamplingRate = 44100

[Output]
#出力デバイスのID
ID = 1
#Record 1: SavePathに出力, 0:IDのデバイスに出力し続ける。
Record = 1
#recording time [sec] >= 1
RecordTime = 15
```

# 設定ファイルの読み込み

config.iniファイル, 設定値を読み込む。
loggerに関しては、[Pythonのloggingモジュールの使い方](https://qiita.com/kwashi/items/576c5b287dfc08d404f3)を参考にしてください。

1. 設定ファイルがあるならconfig_ini.read()で設定ファイルを読み込む。
2. config_ini["設定分類"]["設定値名"]で設定値を読み込む.

読み込んだ設定値は、stringなので、数字はint, floatなどで変換する。
また、0, 1で設定したYes/Noの値は、boolとすることで、True, Falseに変換できる。

```python:utils/config.py
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# ------------

from utils.logConf import logging
logger = logging.getLogger(__name__)

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
      self.MicID = int(config_ini['Microphone']['ID'])
      self.SamplingRate = int(config_ini['Microphone']['SamplingRate'])

      self.OutpuID = int(config_ini['Output']['ID'])
      self.Record = bool(int(config_ini['Output']['Record']))
      self.RecordTime = float(config_ini['Output']['RecordTime'])

    except Exception as e:
      logger.critical("config error {0}".format(e))

```

# 設定値を使用

1. 設定読み込みファイルの設定クラスconfigInitをimportする。
2. Conf = configInit() でインスタンス化し、設定ファイルを読み込む。
3. Conf.設定値名　で使用可能

```python
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
#2020-01-15 17:12:03,929 [config.py:28] INFO     ----設定開始----
#2020-01-15 17:12:03,930 [confTest.py:15] INFO     0                 #MicID

```

# まとめ

以上、pythonの設定ファイルに関してでした。
システムを作るとき、後で外部設定をさせようとしたときに修正が少なくなるため、上記のように簡単にでも設定しておくことをおすすめします。


