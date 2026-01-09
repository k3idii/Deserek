from typing import Any
import deserek
import javaConst
from contextlib import contextmanager

import logging
logger = logging.getLogger("DeserekObj")


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
  def pack_for_deserek(self):
    """ return object that can be used by deserek when packing """
    raise Exception("Implement me - I am interface")


class j_String(JavaLikeObject):
  value = ''
  
  def __init__(self,value):
    self.value=value

  def pack_for_deserek(self):
    return deserek.serTC_STRING(
      value=deserek.serJavaString(
        value=self.value,
      ),
    )




class JavaAbstractBasicField():
  value = None
  typecode = -1

  
  def __init__(self, default=None):
    if default is not None:
      self.value = default
  
  def __repr__(self) -> str:
    return f"{self.__class__.__name__}( {self.typecode} ,  {self.value})"
  
  def set(self, val):
    logger.debug(f"SET {self.__class__.__name__}({self.typecode}) = {self.value}")
    self.value = val
  
  def for_classDesc(self, name):
    return deserek.serPrimitiveDesc(
      typecode = ord(self.typecode),
      fieldName = deserek.serJavaString(value=name)
    )

  def for_classData(self):
    return deserek.serValuePrimitive(
      _typecode_hint=ord(self.typecode),
      value=self.value
      )
 
class JavaInt32(JavaAbstractBasicField):
  typecode = 'I'
 
 
class JavaFloat(JavaAbstractBasicField):
  typecode = 'F'
 

class JavaObjectField():
  typecode = 'L' # object
  value = None
  object_name = "Ljava/lang/Object;"

  def __init__(self, object_name=None, value=None):
    if object_name:
      self.object_name = object_name 
    if value:
      self.value = value
  
  def __repr__(self) -> str:
    return f"ObjectField({self.object_name}, {self.value})"
  
  def set(self, val):
    logger.debug(f" SET {self.__class__.__name__}({self.typecode}/{self.object_name}) => {self.value})")
    self.value = val
    
  def for_classDesc(self, name):
    return deserek.serObjectDesc(
      typecode = ord(self.typecode),
      fieldName = deserek.serJavaString(value=name),
      className1=deserek.serTC_STRING(
        value=deserek.serJavaString(value=self.object_name),
      ),
    )
  
  def for_classData(self):
    return self.value.pack_for_deserek() # object expeced here


class JavaStringField(JavaObjectField):
  object_name = "Ljava/lang/String;"

  def __init__(self, value=""):
    self.value = value
    
  def for_classData(self):
    return j_String(self.value).pack_for_deserek()


class JavaBinaryObjectWriter():
  wire : deserek.bytewirez.Wire = None
  
  def __init__(self):
    self.wire = deserek.bytewirez.Wire()

  def writeInt(self,v):
    self.wire.write_dword(v)



class JavaObjectWriter():
  """ Default function for WriteObject """
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
      self._fields = {}

    self._super_class_list = []
    c = self
    while c != None:
      self._super_class_list.append(c)
      c = c._super_class


    self.constructor()
    logger.debug(f"Object({self.__class__.__name__}, {self._class_name}) initialized !")
    
    # TODO: run this after construcor and use set() function from fields
    for key,val in kw.items():
      setattr(self, key, val)
      

  def constructor(self):
    pass 
  
  
  def get(self, __name:str) -> Any:
    return self._fields[__name].value
  
  #def __getattr__(self, __name: str) -> Any:
  #  print("GETATTR",__name)
  #  if hasattr(self,__name):
  #    print("internal attr")
  #  else:
      

  def set(self, value):
    logger.debug("you should try to implement that for your class")

  def __setattr__(self, __name: str, __value: Any) -> None:
    logger.debug(f"JavaObject->setting [{self.__class__.__name__}]::[{ __name}] => {__value}")
    if hasattr(self,__name):
      # classic way
      self.__dict__[__name] = __value
    else:
      logger.debug(self._fields)
      
      setter = getattr(self._fields[__name], "set", None)
      if setattr and callable(setter):
        logger.debug(f"Call set {__name} => {__value}")
        setter(__value)
      else:
        logger.debug(f"Assign {__name} => {__value}")
        self._fields[__name] = __value
    
  def _get_flags(self):
    flags = 0 | javaConst.SC_SERIALIZABLE
    if callable(self.writeObject):
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
    
    list_of_field_desc = []
    
    for name, obj in self._fields.items():
      logger.debug("~ for class Desc", name)
      list_of_field_desc.append( 
        obj.for_classDesc(name)
      )
      
    obj = deserek.serTC_CLASSDESC(
      className = deserek.serJavaString( value=self._class_name ),
      UID =deserek.serUID( value=self._uid ),
      handle = deserek.serHandle(value=HandleID.next()),
      fields = deserek.serListOfObj( value=list_of_field_desc ),
      classDescFlags = deserek.serClassFlags(value=self._get_flags()),
      classAnnotation = class_an,
      superClassDesc = su_class,
    )
    return obj

  def prepare_standard_fields_values(self,filter=None):
    field_values = []
    
    for name, obj in self._fields.items():
      logger.debug(f" > ClassData-field:{name}=>{obj}")
      if filter and name not in filter:
        logger.debug(f"    ~ SKIP ")
        continue
      field_values.append(
        obj.for_classData()
      )
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
    logger.debug(">> Write values ", kwargs)
    obj = deserek.serClassDescValues(
      _class_name=self._class_name,
      **kwargs,
    )
    return obj
    
  def pack_for_deserek(self):
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
  _fields = {
    'foo' : JavaInt32(52),
    'sss' : JavaStringField("test"),
    "ob1" : JavaObjectField(),
  }
  

class j_TestCustomClass2(JavaSerializableClass):
  _class_name = "customclass2"
  _uid = 2337
  _fields = {
    "foo" : JavaInt32(123),
    "sss" : JavaStringField("test"),
  }
  
  def writeObject(self, wr: JavaObjectWriter):
    self.defaultWriteObject()
    with wr.binary_block() as binwr:
      binwr.writeInt(0xff)
    
    i1 = javaCommons.j_simpleInteger()
    i1.value = 0xeeff
    wr.write(i1.pack_for_deserek())
    





if __name__ == '__main__':
  import sys
  import javaCommons 

  sys.argv.append('3') # 
  test_no = int(sys.argv[1])

  if test_no == 1:
    o = javaCommons.j_simpleInteger()
    o.set(31337)

    x = o.pack_for_deserek()
    print(x)
    print(x.as_python() )

    open("tmp_int1.bin","wb").write( deserek.do_serialize(x))

  if test_no == 11:
    o = javaCommons.j_java_lang_integer()
    o.set( int(sys.argv[2]) )
    j = o.pack_for_deserek()
    print(j)
    open('tmp_int42.bin',"wb").write( deserek.do_serialize(j))


  if test_no == 3:
    print("testcase 3:1")
    tmp = javaCommons.j_java_lang_integer()
    tmp.set(33)

    print("testcase 3:2")
    o = j_TestCustomClass()
    o.foo = 123
    o.sss = "Test"
    o.ob1 = tmp
    print(o)
    
    print("testcase 3:3")
    
    x = o.pack_for_deserek()
    print(x)
    print(x.as_python())
    open('tmp_custom.bin',"wb").write( deserek.do_serialize(x))

  if test_no == 4:
    o = j_TestCustomClass2()
    o.foo = 0xffff
    o.sss = "Test"

    print(o)
    x = o.pack_for_deserek()
    print(x)
    open('tmp_custom2.bin',"wb").write( deserek.do_serialize(x))

   
  
  
  