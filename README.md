# stereophonic-Sound-System

頭部伝達関数(HRTF)を用いた立体音響システム。

# 目的

昨今Vtuberなど仮想空間でキャラクターを動かす職業が増えています。実際に、この職業の方々は、マイク入力を、そのまま、OBSを流しているため、キャラクタの位置に関わらず、視聴者が聞く音声は、1chになっています。
そのため、より没入感のある配信を行うためにも、キャラクタの位置に合わせて、マイク入力を変換するシステムが必要であると考え、立体音響システムを作成しました。


# start project

```bash
git clone https://github.com/k-washi/stereophonic-Sound-System.git
cd ./stereophonic-Sound-System

#仮想環境作成(必要に応じて実行)
python -m venv venv
source venv/bin/activate

#ライブラリのインストール
pip install -r ./requirement.txt
```

# オーディオデバイス情報の取得

```bash
python ./acoustic/acousticSignalProc.py 

#マイク入力, 出力デバイスのID情報を取得
#2020-01-15 15:32:36,638 __main__     INFO     Set Audio Device Info || Index: 0 | Name: Built-in Microphone | ChannelNum: 2, 0 | SampleRate: 44100
#2020-01-15 15:32:36,638 __main__     INFO     Index: 0 | Name: Built-in Microphone | ChannelNum: in 2 out 0 | SampleRate: 44100.0
#2020-01-15 15:32:36,639 __main__     INFO     Index: 1 | Name: Built-in Output | ChannelNum: in 0 out 2 | SampleRate: 44100.0
```

# 設定ファイルの設定

config.iniにデバイス情報などを記載する。
基本的には、環境に合わせて、Microphone, Outputの設定を変更する。
詳細はconfig.iniに記載。

# 音源位置サーバー

音声を立体音響にするための音源位置情報を音源位置サーバーから取得する。

```bash
#サーバーの起動
python ./proto/server.py 
```

音源位置取得はgrpcを用いており、./proto/position.protoのプロトコルファイルを参考にしてください。
grpcで作成しているため、server.pyの__main__処理部分を変更することで、独自に音源位置を与えることが可能になります。
現在は、ServerクラスのposServer.pubPos(x,y,z)関数に、x, y, zの与えることで、現在の音源位置を格納しています。
また、このサーバーに音源位置を与えるプロトコルも作成しているため、別のサービスから音源位置をサーバーに与えることも可能です。

# 立体音響処理クライアント

マイク入力、立体音響処理を行い、立体音響を出力します。

```bash
python ./acoustic/audioStreamOverlapAdder.py 
```

overlap add methodとSIFTを用いて、周波数ごとの情報に変換したマイク入力に対して、音源から右、左耳までのHRTFを畳み込んでいます。
また、ifftの結果に、距離減数を行っています。


# LICENCE

本システムのHRTFは、以下のサイトのデータベースを用いました。

(頭部伝達関数データベース)[http://www.sp.m.is.nagoya-u.ac.jp/HRTF/database-j.html]

西野隆典, 梶田将司, 武田一哉, 板倉文忠, "水平方向及び仰角方向に関 する頭部伝達関数の補間," 日本音響学会誌, 57巻, 11号, pp.685-692, 2001.


