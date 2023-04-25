import deserek
import javaConst
from collections import OrderedDict

WELL_KNOWN = {
  "java.util.HashMap" : 362498820763181265,
  "java.lang.Integer" : 1360826667806852920,
  "java.lang.Number"  : -8742448824652078965,
  
}


javaConst.baseWireHandle

class __HandleIdGeneratorClass:
  n = javaConst.baseWireHandle
  def next(self):
    n = self.n 
    self.n = n + 1
    return n

HandleID = __HandleIdGeneratorClass()






class JavaStuff:
  def to_java(self):
    raise Exception("Implement me - I am interface")

class SingleValue:
  _val = None
  def __init__(self, value=None):
    if value:
      self._val = value 



class JavaStringValue(JavaStuff, SingleValue):
  def to_java(self):
    return deserek.serJavaString(value=self._val)

class JavaStringObject(JavaStuff, SingleValue):
  def to_java(self):
    return deserek.serTC_STRING(
      value = deserek.serJavaString(
        value = self._val 
      )
    )


class JavaField(JavaStuff):
  _name = ''
  _value = ''
  _typecode = -1
  

class JavaSerializableClass(JavaStuff):
  _name = None
  _uid = None
  _annotation = None
  _super_class = None
  _fields = None
  _field_types = {}
  
  _has_write_method = False 
  
  def __init__(self):
    self.constructor()
  
    
  def constructor(self):
    pass 
  
  
  
  def _get_flags(self):
    flags = 0 | javaConst.SC_SERIALIZABLE
    if self._has_write_method:
      flags = flags | javaConst.SC_WRITE_METHOD
    return flags
          
  def create_ClassDesc(self):
    if self._uid is None:
      self._uid = WELL_KNOWN.get(self._class_name, None)
    assert self._uid != None, f"UID cant be empty for class <{self._class_name}>"
    
    
    if self._annotation is None:
      class_an = deserek.serListOfObj(value=[deserek.serTC_ENDBLOCKDATA()])
    else:
      raise Exception("Implement me")
    
    if self._super_class is None:
      su_class = deserek.serTC_NULL()
    else:
      raise Exception("Implement me")
    
    list_of_fields = []
    print(self._fields)
    print(self._field_types)
    for f in self._fields:
      assert f in self._field_types, f"Need field type definition for {f}"
      type_hint = self._field_types[f]
      value = getattr(self, f)

      if type_hint in javaConst.prim_typecode_chr:
        #    primitiveDesc OR objectDesc,
        list_of_fields.append(
          deserek.serPrimitiveDesc(
            typecode = ord(type_hint),
            fieldName = deserek.serJavaString(value=f)
          )
        )
      elif type_hint in javaConst.obj_typecode_chr:
        raise Exception("That stuff is not yet implemented XD")
      else:
        raise Exception(f"Invalid typecode -> {type_hint}")
    
  
    obj = deserek.serTC_CLASSDESC(
      className = deserek.serJavaString( value=self._class_name ),
      UID =deserek.serUID( value=self._uid ),
      handle = deserek.serHandle(value=HandleID.next()),
      fields = deserek.serListOfObj( value=list_of_fields ),
      classDescFlags = deserek.serClassFlags(value=self._get_flags()),
      classAnnotation = class_an,
      superClassDesc = su_class,
    )
    return obj

  def create_ClassData(self):
    data_items = 0
    field_values = []
    for f in self._fields:
      type_hint = self._field_types[f]
      value = getattr(self, f)
      if type_hint in javaConst.prim_typecode_chr:
        field_values.append(
          deserek.serValuePrimitive(
            _typecode_hint=ord(type_hint),
            value=value,
        ))
      else:
        raise Exception("Not implemented !")
    obj = deserek.serClassDescValues(
          _class_name=self._class_name,
          serialdata=deserek.serListOfObj(value=field_values),
          )
    
    return obj
    
  def to_java(self):
    obj = deserek.serTC_OBJECT(
      classDesc = self.create_ClassDesc(),
      handle    = deserek.serHandle(value=HandleID.next()),
      classData = self.create_ClassData(),
      )
    return obj

  
  
  
  
  
  
  
class JavaExternalizableClass(JavaSerializableClass):
  
  def _get_flags(self):
    flags = 0 | javaConst.SC_BLOCK_DATA | javaConst.SC_EXTERNALIZABLE
    return flags

  def create_ClassData(self):
    data_items = []
    # items goes here 
    data_items.append(
      deserek.serTC_ENDBLOCKDATA()
    )
    obj = deserek.serListOfObj(
      value=data_items
    )
    



class j_Integer(JavaSerializableClass):
  _class_name = 'java.lang.Integer'
  _fields = ['value']
  _field_types = {
    'value' : 'I'
  }


if __name__ == '__main__':
  o = j_Integer()
  o.value = -4

  x = o.to_java()
  print(x)
  print(x.as_python() )

  open("tmp_int1.bin","wb").write( deserek.do_serialize(x))

  
  
  
  
  
  
  
  