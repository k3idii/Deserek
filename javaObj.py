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




class JavaLikeObject:
  def to_java(self):
    raise Exception("Implement me - I am interface")

class SingleValue:
  _val = None
  def __init__(self, value=None):
    if value:
      self._val = value 



class JavaStringValue(JavaLikeObject, SingleValue):
  def to_java(self):
    return deserek.serJavaString(value=self._val)

class JavaStringObject(JavaLikeObject, SingleValue):
  def to_java(self):
    return deserek.serTC_STRING(
      value = deserek.serJavaString(
        value = self._val 
      )
    )


class JavaField(JavaLikeObject):
  _class_name = ''
  _value = ''
  _typecode = -1
  

class JavaSerializableClass(JavaLikeObject):
  _class_name = None
  _uid = None
  _annotation = None
  _super_class = None
  _fields = None
  _has_write_method = False 
  
  def __init__(self,**kw):
    if self._fields is None:
      self._fields = {}

    for key,val in kw.items():
      setattr(self, key, val)
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
    assert self._uid != None, f"UID cant be NONE for class <{self._class_name}> or class need to be 'WELL_KNOWN' :) "
    
    if self._annotation is None:
      class_an = deserek.serListOfObj(value=[deserek.serTC_ENDBLOCKDATA()])
    else:
      raise Exception("Implement me")
    
    if self._super_class is None:
      su_class = deserek.serTC_NULL()
    else:
      su_class = self._super_class().create_ClassDesc()
    
    list_of_fields = []
    for name, type_hint in self._fields.items():
      print(f"ClassDesc-field:{name}")
      #assert f in self._field_types, f"Need field type definition for {f}"
      #type_hint = self._field_types[f]
      #value = getattr(self, name)

      if type_hint in javaConst.prim_typecode_chr:
        #    primitiveDesc OR objectDesc,
        list_of_fields.append(
          deserek.serPrimitiveDesc(
            typecode = ord(type_hint),
            fieldName = deserek.serJavaString(value=name)
          )
        )
      elif type_hint == 'string':
        list_of_fields.append(
          deserek.serJavaString(value="Ljava/lang/String;")
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
    for name, type_hint in self._fields.items():
      print(f"ClassData-field:{name}")
      value = getattr(self, name)
      if type_hint in javaConst.prim_typecode_chr:
        field_values.append(
          deserek.serValuePrimitive(
            _typecode_hint=ord(type_hint),
            value=value,
        ))
      elif type_hint == 'string':
        field_values.append(
          deserek.serTC_STRING(
                    value=deserek.serJavaString(
                      value=value,
                      ),
                    ),
        )
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
  _fields = [] # no need to list fields
  
  def _get_flags(self):
    flags = 0 | javaConst.SC_BLOCK_DATA | javaConst.SC_EXTERNALIZABLE
    return flags
  
  def writeExternal(self):
    raise Exception("Implement me !")

  def create_ClassData(self):
    data_items = 0
    field_values = []
    data = b''
    for item in self.writeExternal():
      data += deserek.do_serialize(item, skip_magic=1)
      
    field_values.append(
      deserek.serTC_BLOCKDATA(size=len(data), value=data)
    )
    field_values.append(deserek.serTC_ENDBLOCKDATA())
    
    obj = deserek.serClassDescValues(
      _class_name=self._class_name,
      externalContent=deserek.serListOfObj(value=field_values),
    )
    return obj




class j_TestObjectName(JavaExternalizableClass):
  _class_name = "com.test.ObjectName"
  _uid = 1234

  def writeExternal(self):
    yield deserek.serJavaString(value=self.value)  
  

class j_simpleInteger(JavaSerializableClass):
  '''
  Integer that don't extend java.lang.Number - but works
  '''
  _uid = 1360826667806852920
  _class_name = 'java.lang.Integer'
  _fields = ['value']
  _field_types = {
    'value' : 'I'
  }

class j_java_lang_number(JavaSerializableClass):
  _uid = -8742448824652078965
  _class_name = 'java.lang.Number'
  _fileds = {
    'value' : "I"
  }

class j_java_lang_integer(JavaSerializableClass):
  _uid = 1360826667806852920
  _class_name = 'java.lang.Integer'
  _super_class = j_java_lang_number
  _fields = {
    'value' : 'I'
  }




class j_TestCustomClass(JavaSerializableClass):
  _class_name = "customclass"
  _uid = 1337
  _fields = ['foo']
  _field_types = {
    'foo' : ''
  }
  _fields = {
    'foo' : "Object"
  }




if __name__ == '__main__':
  import sys
  sys.argv.append('3') # 
  test_no = int(sys.argv[1])

  if test_no == 1:
    o = j_Integer()
    o.value = -4

    x = o.to_java()
    print(x)
    print(x.as_python() )

    open("tmp_int1.bin","wb").write( deserek.do_serialize(x))

  if test_no == 11:
    o = j_java_lang_integer()
    o.value = 42
    j = o.to_java()
    print(j)
    open('tmp_int42.bin',"wb").write( deserek.do_serialize(j))


  if test_no == 2:
    o = j_TestName()
    o.value = "foobar"
    x = o.to_java()
    print(x)
    open("tmp_ob1.bin","wb").write( deserek.do_serialize(x))

  if test_no == 3:
    o = j_TestCustomClass()
    print(o)
    x = o.to_java()
    print(x)
    print(x.as_python())
    
  
  
  
  