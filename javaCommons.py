from javaObj import *


class j_simpleInteger(JavaSerializableClass):
  '''
  Integer that don't extend java.lang.Number - but works
  '''
  _uid = 1360826667806852920
  _class_name = 'java.lang.Integer'
  
  def _init_fields(self):
    return [
      JavaBasicField("value", "I", 0)
    ]


class j_java_lang_number(JavaSerializableClass):
  _uid = -8742448824652078965
  _class_name = 'java.lang.Number'
  def _init_fields(self):
    return []

class j_java_lang_integer(JavaSerializableClass):
  _uid = 1360826667806852920
  _class_name = 'java.lang.Integer'
  _super_class = j_java_lang_number

  def _init_fields(self): 
    return [
      JavaBasicField("value", "I")
    ]
  


class j_HashMap(JavaSerializableClass):
  _class_name = "java.util.HashMap"
  _uid = 362498820763181265
  
  MAP = None
  
  def _init_fields(self):
    return  [
      JavaBasicField("loadFactor", "F"),
      JavaBasicField("threshold","I"),
    ]
  
  def constructor(self):
    self.MAP = {}
    self.loadFactor = 0.1
    self.threshold = 2

  def writeObject(self, wr: JavaObjectWriter):
    self.defaultWriteObject()
    size = len(self.MAP)
    with wr.binary_block() as binwr:
      binwr.writeInt(0x00) # bickets
      binwr.writeInt(size)  # size
    for k,v in self.MAP.items():
      wr.write(k.to_deserek())
      wr.write(v.to_deserek())
      



class j_java_net_URL(JavaSerializableClass):
  _class_name = "java.net.URL"
  _uid = -7627629688361524110
  
  def _init_fields(self):
    return  [
      JavaBasicField("hashCode", "I",0),
      JavaBasicField("port","I",0),
      JavaStringField("authority"),
      JavaStringField("file"), 
      JavaStringField("host"), 
      JavaStringField("protocol"), 
      JavaStringField("ref"), 
    ]





