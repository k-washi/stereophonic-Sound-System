# Pythonで始めるgRPC

# 概要

gRPCはあらゆる環境で実行できるモダンで高性能なオープンソースRPC(Remoto Protocol Call)フレームワークです。Protocol Buffersを使ってデータをシリアライズし、高速な通信を実現できるという利点がある。様々な言語やプラットフォームに対応しており、http/2を活かした双方向ストリーミングなどが可能である。Protocol Buffersを使用してシンプルにサービス(通信するデータや関数)を定義でき、APIの仕様を明文化できる。

※この章は[gRPC](https://grpc.io/)を参考にしています。

git: [k-washi/stereophonic-Sound-System/proto](https://github.com/k-washi/stereophonic-Sound-System/tree/master/proto)

Golang versinのgRPCの記事を[Golangで始めるgRPC](https://qiita.com/kwashi/items/533bbb7d09e723c8b56f)に記載しています。

# 内容

ここでは、gRPCを用いてクライアント(python)からのリクエストに対して、サーバーで計算した適当な物体の位置(x, y, z)をレスポンスする手法について説明します。
もともとは、キャラクターの位置に合わせて立体音響を生成するシステムで、位置情報を送信するために作成しました。

# ライブラリのインストール

```bash
pip install grpcio-tools==1.26.0
```

#　プロトコルの定義

以下のように.protoファイルに、Posとしてポジションx, y, zを定義する。
そして、Positionが位置情報を含んだプロトコル(通信規約)となる。一方で、サーバ側へ位置情報を要求するメッセージ、または、位置情報を発行した結果として、Msgのプロトコルを定義する。
また、通信に使用する関数として、PositionReqとPositionPubを定義した。PositionReqは、Msgをサーバーに送信し、Position情報をサーバーから受け取る関数で、PositionPubは、Position情報をサーバーに送信し、Msgを受け取る関数である。本記事では、PositionReqを用いた例で説明する。

```proto:proto/position.proto
syntax = "proto3";

package posXYZ;
option go_package="posXYZpb";

message Pos {
  float x = 1;
  float y = 2;
  float z = 3;
}

//client streaming
message Position{
  Pos position = 1;
  int32 status = 2;
  string msg = 3;
}

message Msg{
  int32 status = 1;
  string msg = 2;
}


service PositionService{
  
  rpc PositionReq(Msg) returns (Position) {};
  rpc PositionPub(Position) returns (Msg) {};
}
```

# python用のprotocol bufferへの変換

Golang versinのgRPCの記事 [Golangで始めるgRPC](https://qiita.com/kwashi/items/533bbb7d09e723c8b56f)に記載しているように、golang用のprotocol bufferに変換した場合でも、本記事のように、python用のprotocol bufferに変換した場合でも、上記のプロトコルの定義に基づいた変換が行われます。このprotoco bufferへの変換により、各言語で定義された、各messageの構造体と、service関数が含まれた定義書(プログラム)が出力されます。

Pythonは、以下のプログラムを実行することで変換できます。

```python:proto/codegen.py
from grpc.tools import protoc

protoc.main(
    (
        '',
        '-I.',
        '--python_out=.',
        '--grpc_python_out=.',
        './proto/position.proto',
    )
)
```

```bash
python ./proto/codegen.py
```

上記のコマンドの結果、プロトコルファイルで定義したmessageを定義したposition_pb2.pyと、gRPC通信に使用する関数を定義したposition_pb2_grpc.pyを生成する。

# サーバー側の実装

ここでは、リクエストMsgを受け取り、Position(位置情報)を発行するサーバを実装する。
ここで発行する位置情報は、(x, y, z) = (0, 0, 0)から距離1ｍを保ちつつ回転する位置とする。

gRPCと関係がない設定に関するconfigInitや、ロギングに関するloggerに関しては、私の過去記事である、[python configparser によるパラメータ設定](https://qiita.com/kwashi/items/3a6df37978d811b48cfa), [Pythonのloggingモジュールの使い方](https://qiita.com/kwashi/items/576c5b287dfc08d404f3)を参考にしてください。

PositionServerクラスは、position_pb2_grpc.pyに定義されたPositionServerServerをオーバーロードし、requestに対して位置情報を返すPositionReq関数を定義する。この返り値であるPositionは、position_pb2.pyに定義されたものを使用している。また、このクラスでは、位置情報x, y, zを保存、出力する関数も定義し、位置情報を管理している。

Serverクラスは、gRPCのサーバー側が行う処理をまとめたクラスである。そのため、PosotionServerクラスのインスタンスを変数として持っている。
start関数は、gRPCサーバーを開始する処理を定義し、stop関数にgRPCサーバーを停止する処理を定義している。これらのstart, stopの処理は定形文であるため、基本的な流れはどのプログラムにおいても変わらない。

main処理では、start関数を実行することで、サーバーを開いたことになり、gRPCのサーバー側の処理は以上となる。
ここでは、時間ごとに位置情報を変化させるため、posServer.pubPos(x,y,z)で発行する位置情報を上書きしている。

```python:proto/server.py
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# ------------

from utils.config import configInit
Conf = configInit()
logger = Conf.setLogger(__name__)

# ------------
#grpc

import grpc
from proto.position_pb2 import *
from proto import position_pb2_grpc

# ------------

from concurrent import futures

class PositionService(position_pb2_grpc.PositinServiceServicer):
  def __init__(self):
    self.x = 1.
    self.y = 0.
    self.z = 0.

  def PositionReq(self, request, context):
    try:
      is_success = 0
    except:
      is_success = -1
    return Position(
      position = Pos(
        x = self.x, y = self.y, z = self.z
      ),
      status = is_success,
      msg = "character position"
    )

  def pubPos(self, x, y, z):
    self.x, self.y, self.z = x, y, z
  
  def getPos(self, x, y, z):
    return self.x, self.y, self.z

class Server():
  def __init__(self):
    self.posServer = PositionService()

  def start(self):
    
    self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=3))
    position_pb2_grpc.add_PositinServiceServicer_to_server(
      self.posServer, self.server
    )

    self.server.add_insecure_port(Conf.PosServer)
    self.server.start()
    logger.info("Start server {0}".format(Conf.PosServer))

  def stop(self):
    self.server.stop(0)

if __name__ == "__main__":
  import time
  import numpy as np
  server = Server()
  server.start()
  
  z = 0.
  azimuth = 0.
  aziShift = 5* np.pi / 180.

  def azi2pos(azimuth):
    x = np.cos(azimuth)
    y = np.sin(azimuth)
    return x, y

  try:
    while True:
      time.sleep(0.1)
      azimuth += aziShift
      x,y = azi2pos(azimuth)
      server.posServer.pubPos(x,y,z)

  except Exception as e:
    logger.critical(e)
    server.stop()
```

# クライアント側の実装

クライアント側の実装は、posClientクラスに実装している。open関数でクライアント処理を開始します。ここでは、position_pb2_grpc.PositinServiceStubにクライアント側が実行する関数が格納されていることに注意してください。そのため、posRequest関数において、self.stub.PositionReq関数によりMsgを送信し、返り値としてサーバからの情報を取得できます。
あとは、mainの処理の中で、posRequest()を実行するごとに、サーバー側と通信し、位置情報を取得できます。

```python:proto/client.py
mport os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# ------------

from utils.config import configInit
Conf = configInit()
logger = Conf.setLogger(__name__)

# ------------
#grpc

import grpc
from proto.position_pb2 import *
from proto import position_pb2_grpc

class posClient():
  def __init__(self):
    self.x = 0.
    self.y = 0.
    self.z = 0.

  def posRequest(self):
    request = Msg(
      status = 0,
      msg = "request pos"
    )
    res = self.stub.PositionReq(request)
    if res.status == 0:
      logger.info("PositionRes {0}, {1}, x:{2}, y:{3}, z:{4}".format(res.status, res.msg, res.position.x, res.position.y, res.position.z))
      self.x, self.y, self.z = res.position.x, res.position.y, res.position.z
      return True
    
    logger.error("Position Response Error")
    return False

  
  def open(self):
    self.channel = grpc.insecure_channel(Conf.PosClient)
    self.stub = position_pb2_grpc.PositinServiceStub(self.channel)
    logger.info("Open position client channel: {0}".format(Conf.PosClient))

  def close(self):
    self.channel.close()
  
  def getPos(self):
    return self.x, self.y, self.z
  
if __name__ == "__main__":
  import time
  posCl = posClient()
  posCl.open()
  while True:
    time.sleep(1)
    try:
      ok = posCl.posRequest()
      if ok:
        x, y, z = posCl.getPos()
        logger.info("{0}, {1}, {2}".format(x, y, z))
    except Exception as e:
      logger.error("client error {0}".format(e))
  posCl.close()
```


# まとめ

以上で、pythonによるgRPCで、位置情報のやりとりができました。
gRPCは、多言語で書かれたマイクロサービスを構築がより簡単になったりするなどの利点があるため、今後多くの場面で使われる技術になると思います。
ぜひ、一度試してみてください。
