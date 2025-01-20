from typing import Any
import deserek
import javaConst
from contextlib import contextmanager


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
  def to_deserek(self):
    raise Exception("Implement me - I am interface")


class j_String(JavaLikeObject):
  value = ''
  
  def __init__(self,value):
    self.value=value

  def to_deserek(self):
    return deserek.serTC_STRING(
      value=deserek.serJavaString(
        value=self.value,
      ),
    )
  

class JavaBasicField():
  value = None
  typecode = -1
  name = None
  
  def __init__(self, name, typecode, default=0):
    self.typecode = typecode 
    self.name = name
    if default is not None:
      self.value = default
  
  def __repr__(self) -> str:
    return f"BasicField : {self.name} -> {self.typecode} / {self.value}"
  
  def for_classDesc(self):
    return deserek.serPrimitiveDesc(
      typecode = ord(self.typecode),
      fieldName = deserek.serJavaString(value=self.name)
    )

  def for_classData(self):
    return deserek.serValuePrimitive(
      _typecode_hint=ord(self.typecode),
      value=self.value
      )
 
 

class JavaObjectField():
  typecode = 'L' # object
  value = None
  name = None
  object_name = "Ljava/lang/Object;"

  def __init__(self, name, object_name=None):
    if object_name:
      self.object_name = object_name 
    self.name = name
  
  def __repr__(self) -> str:
    return f"ObjectField : {self.name} -> {self.value}"
    
  def for_classDesc(self):
    return deserek.serObjectDesc(
      typecode = ord(self.typecode),
      fieldName = deserek.serJavaString(value=self.name),
      className1=deserek.serTC_STRING(
        value=deserek.serJavaString(value=self.object_name),
      ),
    )
  
  def for_classData(self):
    return self.value.to_deserek() # objecr expeced here


class JavaStringField(JavaObjectField):
  object_name = "Ljava/lang/String;"

  def __init__(self, name):
    self.name = name
    self.value = ""

  def for_classData(self):
    return j_String(self.value).to_deserek()

class JavaBinaryObjectWriter():
  wire : deserek.bytewirez.Wire = None
  
  def __init__(self):
    self.wire = deserek.bytewirez.Wire()

  def writeInt(self,v):
    self.wire.write_dword(v)



class JavaObjectWriter():
  item_stack: list = None

  def __init__(self):
    self.item_stack = []

  def write(self, item):
    self.item_stack.append(item)

  def get_items(self):
    return self.item_stack
  
  @contextmanager
  def binary_block(self):
    obj = JavaBinaryObjectWriter()
    try:
      yield obj
    finally:
      blob = obj.wire.dump()
      self.write(
        deserek.serTC_BLOCKDATA(
          size=len(blob),
          value=blob,
        )
      )


class JavaSerializableClass(JavaLikeObject):
  _class_name = None
  _uid = None
  _annotation = None
  _super_class = None
  _fields = None
  _super_class_list = None
  _standard_fields_values = None

  writeObject = None # override this to implement cutom writer
  
  def __init__(self,**kw):
    if self._fields is None:
      self._fields = []

    self._fields = self._init_fields() 

    self._super_class_list = []
    c = self
    while c != None:
      self._super_class_list.append(c)
      c = c._super_class

    for key,val in kw.items():
      setattr(self, key, val)
    self.constructor()
    print(f"Object {self.__class__.__name__} / {self._class_name} initialized !")
  
  def _init_fields(self):
    raise Exception("MUST HAVE FIELDS !")
  
  def constructor(self):
    pass 
  
  def DISABLED__getattr__(self, __name: str) -> Any:
    print("GETATTR",__name)
    for fld in self._field_generator():
      if fld.name == __name:
        return fld

  def get(self, __name:str) -> Any:
    for fld in self._field_generator():
      if fld.name == __name:
        return fld.value


  def x__getattr__(self, __name: str) -> Any:
    print("GETATTR",__name)
    for fld in self._field_generator():
      if fld.name == __name:
        return fld.value

  def __setattr__(self, __name: str, __value: Any) -> None:
    print(f"setting [[{self.__class__.__name__}]] -> [[{ __name}]] to {__value}")
    if hasattr(self,__name):
      self.__dict__[__name] = __value
    else:
      for f in self._field_generator():
        if f.name == __name:
          f.value = __value
    
    
  def _get_flags(self):
    flags = 0 | javaConst.SC_SERIALIZABLE
    if callable(self.writeObject):
      flags = flags | javaConst.SC_WRITE_METHOD
    return flags
  


  def _field_generator(self):
    print(">FieldGenrator", self._super_class_list)
    for c in self._super_class_list[::-1]:
      print(f" Getting fields for class {c.__class__.__name__} {c._fields}")
      for f in c._fields:
        print(f"  Field: {f}")
        yield f
    print("<FieldGenerator")

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
    for field in self._fields: # self._field_generator():
      print(f" > ClassDesc-field:{field}")
      list_of_fields.append(
        field.for_classDesc(),
      )
      
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

  def prepare_standard_fields_values(self,filter=None):
    field_values = []
    for field in self._field_generator():
      print(f" > ClassData-field:{field}")
      if filter:
        if field.name not in filter:
          print(f"    ~ SKIP ")
          continue
      field_values.append(field.for_classData())
    return field_values

  def defaultWriteObject(self): # mimic Java style  writing
    self._standard_fields_values = self.prepare_standard_fields_values()


  def create_ClassData(self):
    kwargs = {}
    if not callable(self.writeObject) :
      kwargs['serialdata'] = deserek.serListOfObj(
        value = self.prepare_standard_fields_values()
      )
    else:
      wr = JavaObjectWriter()
      self.writeObject(wr)

      kwargs['objectAnnotation'] = deserek.serListOfObj(
        value = wr.get_items() + [deserek.serTC_ENDBLOCKDATA()]
      )
      if self._standard_fields_values:
        kwargs['serialdata'] = deserek.serListOfObj(
          value = self._standard_fields_values
        )
    print(">> Write values ", kwargs)
    obj = deserek.serClassDescValues(
      _class_name=self._class_name,
      **kwargs,
    )
    return obj
    
  def to_deserek(self):
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
  






class j_TestCustomClass(JavaSerializableClass):
  _class_name = "customclass"
  _uid = 1337
  def _init_fields(self):
    return [
      JavaBasicField("foo", "I"),
      JavaStringField("sss"),
      JavaObjectField("obj1")
    ]


class j_TestCustomClass2(JavaSerializableClass):
  _class_name = "customclass2"
  _uid = 2337
  def _init_fields(self):
    return  [
      JavaBasicField("foo", "I"),
      JavaStringField("sss"),
    ]
  
  def writeObject(self, wr: JavaObjectWriter):
    self.defaultWriteObject()
    with wr.binary_block() as binwr:
      binwr.writeInt(0xff)
    
    i1 = j_simpleInteger()
    i1.value = 0xeeff
    wr.write(i1.to_deserek())
    


if __name__ == '__main__':
  import sys
  import javaCommons 

  sys.argv.append('3') # 
  test_no = int(sys.argv[1])

  if test_no == 1:
    o = javaCommons.j_simpleInteger()
    o.value = 31337

    x = o.to_deserek()
    print(x)
    print(x.as_python() )

    open("tmp_int1.bin","wb").write( deserek.do_serialize(x))

  if test_no == 11:
    o = javaCommons.j_java_lang_integer()
    o.value = 42
    j = o.to_deserek()
    print(j)
    open('tmp_int42.bin',"wb").write( deserek.do_serialize(j))


  if test_no == 3:
    tmp = javaCommons.j_java_lang_integer()
    tmp.value = 33

    o = j_TestCustomClass()
    o.foo = 8765123
    o.sss = "Test"
    o.obj1 = tmp

    print(o)
    x = o.to_deserek()
    print(x)
    print(x.as_python())
    open('tmp_custom.bin',"wb").write( deserek.do_serialize(x))

  if test_no == 4:
    o = j_TestCustomClass2()
    o.foo = 0xffff
    o.sss = "Test"

    print(o)
    x = o.to_deserek()
    print(x)
    open('tmp_custom2.bin',"wb").write( deserek.do_serialize(x))

   
  
  
  