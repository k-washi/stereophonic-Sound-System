import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# ------------

from utils.config import configInit
Conf = configInit()
print(Conf.PosServer)
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







