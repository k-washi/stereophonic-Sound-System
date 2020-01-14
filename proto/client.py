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
  #posCl.close()

