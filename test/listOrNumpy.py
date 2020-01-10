import numpy as np

import time

"""
list operation 4.133939743041992e-06
np2list operation 3.3020973205566406e-07
numpy operation 0.002478501796722412
"""

list1 = []
list2 = [i for i in range(1024)]

nlist1 = np.array([])
nlist2 = np.array([i for i in range(1024)])

counter = 1000

st = time.time()

for _ in range(counter):
  list1 += list2

cTime = (time.time() - st)/counter
print("list operation {0}".format(cTime))

st = time.time()

for _ in range(counter):
  list1 += nlist1.tolist()

cTime = (time.time() - st)/counter
print("np2list operation {0}".format(cTime))

st = time.time()

for _ in range(counter):
  nlist1 = np.concatenate((nlist1, nlist2), axis=0)

cTime = (time.time() - st)/counter
print("numpy operation {0}".format(cTime))