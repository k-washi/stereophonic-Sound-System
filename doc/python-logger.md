# Pythonのloggingモジュールの使い方

pythonのlogginモジュールの設定を一元管理し、以下のように、日時、ログを書き出したファイル名、 ログレベル(debug, info, error, ...), 出力メッセージと、一貫したフォーマットで出力させる方法を記載します。

```bash
2020-01-15 16:54:52,751 [logTest.py:9] INFO     メッセージです。
```

※　とりあえず、使うことができれば良い人向けです。(ログをローカルに吐き出すなどの処理に関しては説明していません。)
Git: [k-washi](https://github.com/k-washi/stereophonic-Sound-System)
python ver: 3.6.8
## ログの設定

logConf.pyファイルで、formatやログレベルを管理します。

```python:utils/logConf.py 
import logging

format="%(asctime)s [%(filename)s:%(lineno)d] %(levelname)-8s %(message)s"

logging.basicConfig(level=logging.DEBUG, format=format)
```

#　ログの処理

ログ処理を行うファイルで、

1. logConf.pyまでパスを通す
2. __name__で使用するファイルにおけるロガーを設定

を行います。
そして、logger.nfoやlogger.errorによりロギングできます。

```python
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.logConf import logging
logger = logging.getLogger(__name__)

logger.info("メッセージです。")
logger.error("エラーです。")

"""
2020-01-15 16:54:52,751 [logTest.py:9] INFO     メッセージです。
2020-01-15 16:54:52,751 [logTest.py:10] ERROR    エラーです。
"""
```

# まとめ

以上で、簡単なロギング処理が可能となりました。
もし、追加でログのファイル出力等を行う場合、logConf.pyファイルを変更していけば、追加機能も簡単に追加できます。


