from javaObj import *



 
 
 
class j_simpleInteger(JavaSerializableClass):
  '''
  Integer that don't extend java.lang.Number - but works
  '''
  _uid = 1360826667806852920
  _class_name = 'java.lang.Integer'
  _fields ={
    "value" : JavaInt32(0)
  }
  
  def set(self, val):
    self.value.value = val
  

class j_java_lang_number(JavaSerializableClass):
  _uid = -8742448824652078965
  _class_name = 'java.lang.Number'


class j_java_lang_integer(JavaSerializableClass):
  _uid = 1360826667806852920
  _class_name = 'java.lang.Integer'
  _super_class = j_java_lang_number
  _fields ={
    "value" : JavaInt32(0)
  }
  
  def set(self, val):
    self._fields['value'].value = val


class j_HashMap(JavaSerializableClass):
  _class_name = "java.util.HashMap"
  _uid = 362498820763181265
  
  MAP = None
  
  _fields = {
    "loadFactor" : JavaFloat(0),
    "threshold"  : JavaInt32(0),
  }
    
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
      #print("pack k :",k)
      wr.write(k.pack_for_deserek())
      #print("pack v :",v)
      wr.write(v.pack_for_deserek())
      



class j_java_net_URL(JavaSerializableClass):
  _class_name = "java.net.URL"
  _uid = -7627629688361524110
  
  _fields = {
    "hashCode"  : JavaInt32(0),
    "port"      : JavaInt32(0),
    "authority" : JavaStringField(),
    "file"      : JavaStringField(),
    "host"      : JavaStringField(),
    "protocol"  : JavaStringField(),
    "ref"       : JavaStringField(), 
  }
  





