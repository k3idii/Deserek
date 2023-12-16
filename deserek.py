
from collections import OrderedDict

import base64 
import struct

import bytewirez.bytewirez as bytewirez

try:
  from loguru import logger
except:
  print("No loguru ! -> fallback to default")
  from logging import Logger
  logger = Logger("foo")


import yaml
import json

import javaConst

import time


MODULENAMEPREFIX="deserek."

_tc_from_name = lambda name: getattr(javaConst, name)

_tc_map   = dict()
for _item in filter(lambda x:x.startswith('TC_'), javaConst.__dict__):
  _tc_map[getattr(javaConst, _item)] = _item

_tc_to_name = lambda tc: _tc_map[tc]


def _get_sc_flags():
  return list(filter(lambda x:x.startswith('SC_'), javaConst.__dict__))  

def _check_flag(name, value):
  return getattr(javaConst, name) & value
  
def _classDescFlags_to_fields(flg):
  rv = []
  if flg & javaConst.SC_SERIALIZABLE and flg & javaConst.SC_EXTERNALIZABLE:
    raise Exception("FLAG CONFLICT !")
  
  if flg & javaConst.SC_SERIALIZABLE :
    rv.append('serialdata')
  if flg & javaConst.SC_WRITE_METHOD :
    rv.append('objectAnnotation')
  if flg & javaConst.SC_EXTERNALIZABLE:
    if flg & javaConst.SC_BLOCK_DATA:
      rv.append('externalContent')
    else:
      rv.append('objectAnnotation')
  return rv


def _dictify(o):
  if getattr(o,'to_dict',None) is not None:
    return { str(type(o).__name__) : o.to_dict() }
  if type(o) is list:
    #print(o)
    #1/0
    return [_dictify(x) for x in o]
  #print(f"{o} NO JSON")
  return o # the value itself (should be primitive value)



def _cname(o):
  return type(o).__name__

yaml.add_representer(OrderedDict, lambda dumper, data: dumper.represent_mapping('tag:yaml.org,2002:map', data.items()))
def yamlify(o, width=1000):
  return yaml.dump(_dictify(o), default_flow_style=False,  width=width)

class EndBlockData(Exception):
  pass

class ReadCheckFailed(Exception):
  pass
 

PRINT_PADDING='  '
def _get_pad(i):
  return PRINT_PADDING * i

def _strval(o): # ugly way to do that :)
  return json.dumps(o) 

def _int_to_str(v):
  #return str(v)
  #return f'0x{v:x}'
  return f'{v}, # hex: {hex(v)} '

def _pythonize(item, indent):
  #indent+=1
  # print(f"Pythonize {item}")
  can_py = getattr(item,"as_python",None)
  if can_py:
    return can_py(indent)
  elif type(item) == bytes:
    return str(item)
  elif type(item) == int:
    return _int_to_str(item)
  else:
    return _strval(item)
  



class _abs_serBareObj:

  def __init__(self, ctx=None, **kw):
    self._kwargs = kw
    self.init()
    if ctx is not None:
      self._init_from_ctx(ctx)
    else:
      #logger.info(f"Make object [{_cname(self)}] from ({list(kw.keys())})")
      self._init_from_kwargs()
  
  def init(self):
    pass
    
  def _init_from_ctx(self, ctx):
    self.read(ctx)
    
  def _init_from_kwargs(self):
    pass
  
  def read(self, ctx):
    raise Exception(f"Implement READ -> read in {_cname(self)}")

  def write(self, ctx):
    raise Exception(f"Implement WRITE -> write in {_cname(self)}")

  def _args_to_str(self):
    return ' raise Exception("implement me") '
  
  def _args_to_python(self, indent=0):
    return ' raise Exception("implement me") '
  
  def __str__(self):  
    args = self._args_to_str()
    return f"{_cname(self)}({args})"
  
  def __repr__(self):
    return f"OBJECT::{_cname(self)}"

  def as_python(self, indent=0):
    args = self._args_to_python(indent+1)
    # pad = indent * PRINT_PADDING
    return f"{MODULENAMEPREFIX}{_cname(self)}({args})"




class serListOfObj(_abs_serBareObj):
  value = None

  def init(self):
    self.value = []
  
  def _init_from_kwargs(self):
    self.value = self._kwargs.get('value',[])
    #logger.debug(f"List got {len(self.value)} elements")

  def append(self, x):
    self.value.append(x)

  def to_dict(self):
    return [_dictify(x) for x in self.value]

  def get_simple_value(self):
    return list(
      x.get_simple_value() for x in self.value
    )

  def __iter__(self):
    return self.value.__iter__()

  def write(self, ctx, include_size=None):
    ctx.log_inf("WRITE LIST")
    if include_size is not None:
      ctx.wire.write_fmt(include_size, len(self.value))
    for i, item in enumerate(self.value):
      ctx.log_inf(f" WRITE item {i+1} of {len(self.value)}")
      item.write(ctx)

  def _args_to_str(self):
    str_args = []
    for item in self.value:
      s = str(item)
      str_args.append( s )
    return '[ '+(', '.join(str_args))+' ]'

  def _args_to_python(self, indent=0):
    pad = _get_pad(indent)
    str_args = []
    for item in self.value:
      s = _pythonize(item, indent)
      str_args.append( s )
    return '\n'.join([
      f"value=[",
      pad + f",\n{pad}".join(str_args),
      f"{pad}]"
      ])     
    #f'{pad}[\n'+(',\n{pad}'.join(str_args))+' ]'




class _abs_serBasicObject(_abs_serBareObj):
  _kwargs = None
  _fields = []

  def init(self):
    self._fields = self._fields + [] # drop reference

  def _init_from_kwargs(self):
    for key,val in self._kwargs.items():
      if key.startswith('_'): # skip non-fields
        continue
      # logger.info(f"Setup: {_cname(self)}->{key} = <{_dictify(val)}>")
      setattr(self,key, val)    
    self.setup_from_kwargs()
   
  def setup_from_kwargs(self):
    #logger.info(f"Empty setup_from_kwargs @ {_cname(self)}")
    pass  

  def read(self, ctx):
    if self._check_stuff(ctx):
      with ctx.reader.start_object(_cname(self)):  
        self._check_ok(ctx)
        return self.read_obj(ctx)
    
  def _check_stuff(self, ctx):
    return True
  
  def _check_ok(self, ctx):
    pass
  
  def read_obj(self, ctx):
    raise Exception(f"Implement READ_OBJ -> in {_cname(self)}")

  def write(self, ctx):
    ctx.log_inf(f"WRITE_OBJ : {_cname(self)}")
    self._pre_write(ctx)
    return self.write_obj(ctx) # to look same as read_obj 

  def _pre_write(self, ctx):
    pass

  def write_obj(self, ctx):
    raise Exception(f"Implement WRITE_OBJ -> in {_cname(self)}")

  def __repr__(self):
    return str(self)

  def to_dict(self):
    return  _cname(self)

  def _args_to_str(self):
    if len(self._fields) > 0:
      l = list(f"{key}={str(getattr(self, key, 'WTF'))}" for key in self._fields)
      return ", ".join(l)
    else:
      return ""
    
  def _args_to_python(self, indent=0): 
    pad = _get_pad(indent)
    #print(f" {_cname(self)} -> to python {self._fields}" )
    if len(self._fields) > 0:
      ret_str = f"\n"
      for key in self._fields:
        val = _pythonize(getattr(self, key), indent)
        ret_str += f'{pad}{key}={val},\n'
      ret_str += f"{pad}" 
      return ret_str
      
    else:
      return ""
    
  def to_dict(self):
    fields = OrderedDict()
    for key in self._fields:
      fields[key] = _dictify( getattr(self, key) )
    return fields
    

class _abs_serSingleValue(_abs_serBasicObject):
  _fields = ['value']
  value = None
  


class _abs_serTCValue(_abs_serBasicObject):
  TC = -1
  _is_empty = False
    
  def init(self):
    super().init()
    self._tc_name = _tc_to_name(self.TC)
    if self._is_empty:
      self.read_obj = lambda  ctx: ctx.log_dbg(f"<READ EMPTY {_cname(self)}>")
      self.write_obj = lambda ctx: ctx.log_dbg(f"<WRITE EMPTY {_cname(self)}>")
  
  def _check_stuff(self, ctx):
    b = ctx.wire.peek_byte()  
    result = self.TC == b
    r = " YES " if result else " NO "
    ctx.log_dbg(f"CHECK IF : 0x{b:02X}/{b} == {self.TC}/{self._tc_name}/{_cname(self)} -> {r}")
    
    if result:

      return True
    # else:
    raise ReadCheckFailed(f"{b} != {self.TC}")
  
  def _check_ok(self, ctx):
    ctx.reader.will_read("TC")
    ctx.wire.read_byte()
    
    
  def _pre_write(self, ctx):
    ctx.log_inf(f"WRITE TC: 0x{self.TC:02X}")
    ctx.wire.write_byte(self.TC)
  
  def get_simple_value(self):
    return f"<{self._tc_name}>"


class _abs_serPeekTypecode(_abs_serBasicObject):
  _good_values = []
  typecode = -1
  
  def init(self):
    self._fields = ['typecode'] + self._fields
  
  def _check_stuff(self, ctx):
    b = ctx.wire.peek_byte()  
    result = b in self._good_values
    r = " YES " if result else " NO "
    ctx.log_dbg(f"CHECK IF : 0x{b:02X}/{b} == {self._good_values} AT {_cname(self)} -> {r}")
    
    if result:
      return True
    # else:
    raise ReadCheckFailed(f"{b} not in {self._good_values}")
  
  def _check_ok(self, ctx):
    ctx.reader.will_read("typecode")
    self.typecode = ctx.wire.read_byte()

  def write(self, ctx):
    ctx.wire.write_byte(self.typecode)
    self.write_obj(ctx)







class serHandle(_abs_serSingleValue):

  def read(self, ctx):
    ref = self._kwargs.get('ref')
    assert ref is not None, "ref must not be none !"
    
    self.value = javaConst.baseWireHandle + ctx.next_handle_number()
    ctx.log_inf(f"newHandle : {self.value:08x} -> {_cname(ref)} ")
    ctx.register_object(self.value, ref)


  def write(self, ctx):
    pass

  
  

class serClassFlags(_abs_serSingleValue):
  
  def read_obj(self, ctx):
    ctx.reader.will_read("value")
    self.value = ctx.wire.read_byte()
    ctx.log_inf(f"ClassFlags : {self.value}/{self.value:02X}")

  def write_obj(self, ctx):
    ctx.wire.write_byte(self.value)
    
  def explain(self):
    r = []
    for flag in _get_sc_flags():
      if _check_flag(flag, self.value):
        r.append(flag)
    return f"0x{self.value:02x}:" + "|".join(r)
  
  def _args_to_python(self, indent=0):
    r = ['0']
    for flag in _get_sc_flags():
      if _check_flag(flag, self.value):
        r.append(f'javaConst.{flag}')
    return 'value=' + "|".join(r)
  
  
  
class serUID(_abs_serSingleValue):
  
  def read_obj(self, ctx):
    ctx.reader.will_read("value")
    self.value = ctx.wire.read_sqword()
    ctx.log_dbg(f"clsUID=0x{self.value:08x}/{self.value}")

  def write(self, ctx):
    ctx.wire.write_sqword(self.value)

  
class serJavaString(_abs_serSingleValue):

  def read_obj(self, ctx):
    ctx.reader.will_read("size")
    size = ctx.wire.read_word()
    
    ctx.log_dbg(f"try read string len : {size} / 0x{size:04X}")
    
    ctx.reader.will_read("value")
    tmp = ctx.wire.readn(size)
    self.value = tmp.decode()
    
    ctx.log_dbg(f"++ Java::String ({size}){self.value}")
  
  def write(self, ctx):
    ctx.log_inf("JavaString")
    ctx.wire.write_word( len(self.value) )
    ctx.wire.write(self.value.encode())

  
class serJavaLongString(_abs_serSingleValue):

  def read_obj(self, ctx):
    99/0 # TODO 
    self.raw = ctx.wire.read_qword()
    size = struct.unpack(">Q", self.raw)[0]
    ctx.log_dbg(f"read string len : {size} / 0x{size:04X}")

    tmp = ctx.io.read(size)
    self.raw += tmp
    self.value = tmp.decode()
    ctx.log_inf(f"JavaString ({size}){self.value}")

  def write(self, ctx):
    ctx.log_inf("JavaString")
    ctx.wire.write_qword( len(self.value) )
    ctx.wire.write(self.value.encode())

  
  
  
    


class serPrimitiveDesc(_abs_serPeekTypecode):
  _fields = ['fieldName']
  _good_values = javaConst.prim_typecode

  def read_obj(self,ctx):
    #print(f"FIELDS : {self._fields}")
    ctx.log_inf(f"Read primitive {self.typecode}/{chr(self.typecode)}")
    #self.typecode = self._byte
    
    ctx.reader.will_read("fieldName")
    self.fieldName = serJavaString( ctx = ctx )
    ctx.log_dbg(f"FieldName : [{self.fieldName.value}]")

  def write_obj(self, ctx):
    self.fieldName.write(ctx)


def read_primitiveDesc(ctx):
  return serPrimitiveDesc(ctx=ctx)





class serObjectDesc(_abs_serPeekTypecode):
  _fields = ['fieldName', 'className1']
  _good_values = javaConst.obj_typecode
  
  def read_obj(self, ctx):
    ctx.log_inf(f"Read objecDesc {self.typecode}/{chr(self.typecode)}")
    ctx.reader.will_read("fieldName")
    self.fieldName = serJavaString( ctx = ctx )
    ctx.reader.will_read("className1")
    self.className1 = read_object(ctx)
    ctx.log_inf(f"className1 READ-AS XXXXXX {self.className1.__class__} ")
    # serJavaString( deser = ctx )

  def write_obj(self, ctx):
    self.fieldName.write(ctx)
    self.className1.write(ctx)    



def read_objectDesc(ctx):
  return serObjectDesc(ctx=ctx)


class serTC_CLASS(_abs_serTCValue):
  TC = javaConst.TC_CLASS
  _fields = [
    'classDesc',
    'handle'
  ]

  def read_obj(self, ctx):
    ctx.reader.will_read('classDesc')
    self.classDesc = read_classDesc(ctx)

    self.handle = serHandle(ctx=ctx, ref=self)


  def write_obj(self, ctx):
    self.classDesc.write(ctx)
    # handle 
  
    

class serTC_PROXYCLASSDESC(_abs_serTCValue):
  TC = javaConst.TC_PROXYCLASSDESC

  _fields = [
    'handle',
    'count',
    'proxyInterfaceName',
    'classAnnotation',
    'superClassDesc',
  ]
  
  def _get_name(self):
    return '<PROXY CLASS>'

  def read_obj(self, ctx):
    self.handle = serHandle(ctx=ctx, ref=self) 
    ctx.log_inf("TC_PROXYCLASSDESC/proxyClassDescInfo")
    ctx.reader.will_read("count")
    self.count = ctx.wire.read_dword()
    
    ctx.reader.will_read("interfaces")
    with ctx.reader.start_list():
      self.proxyInterfaceName = serListOfObj()
      for i in range(self.count):
        item = serJavaString( ctx = ctx )
        self.proxyInterfaceName.append(item)
  
      #ctx.reader.will_read("class_annotation")
      self.classAnnotation = read_classAnnotation(ctx, info='TC_PROXYCLASSDESC/proxyClassDescInfo/classAnnotation')
      
      #ctx.reader.will_read("super_class")
      self.superClassDesc = read_superClassDesc(ctx)


  def write_obj(self, ctx):
    ctx.wire.write_dword(self.count)
    self.proxyInterfaceName.write(ctx)
    self.classAnnotation.write(ctx)
    self.superClassDesc.write(ctx)


class serTC_CLASSDESC(_abs_serTCValue):
  TC = javaConst.TC_CLASSDESC
  
  _fields = [
    'className',
    'UID',
    'handle',
    'classDescFlags',
    'fields', 
    'classAnnotation', 
    'superClassDesc'
  ]

  def _get_name(self):
    return self.className.value
  
  #className serialVersionUID newHandle classDescInfo
  def read_obj(self, ctx):
    ctx.reader.will_read("className")
    self.className = serJavaString( ctx = ctx )
    
    ctx.reader.will_read("classUUID")
    self.UID = serUID( ctx = ctx )
    
    self.handle = serHandle(ctx=ctx, ref=self) 
      
    ctx.reader.will_read("classFlags")
    self.classDescFlags = serClassFlags(ctx=ctx)
    
    self.fields = self.read_fields(ctx)
    
    ctx.reader.will_read("classAnnotation")
    self.classAnnotation = read_classAnnotation(ctx, info='TC_CLASSDESC/classDescInfo/classAnnotation')
    
    ctx.reader.will_read("superClass")
    self.superClassDesc = read_superClassDesc(ctx)
  
    

  def read_fields(self, ctx):
  
    ctx.reader.will_read("number_of_fields")
    count = ctx.wire.read_word()
    ctx.log_dbg(f"TC_CLASSDESC fields count:{count}")
    
    val = serListOfObj()
    ctx.reader.will_read("fields")
    with ctx.reader.start_list():
      for i in range(count):
        ctx.log_dbg(f"field {i+1}/{count}")
        f = read_fieldDesc(ctx)
        val.append(f)
      return val




  def write_obj(self, ctx):
    self.className.write(ctx)
    self.UID.write(ctx)
    self.classDescFlags.write(ctx)
    self.fields.write(ctx, include_size=">h")
    self.classAnnotation.write(ctx)
    self.superClassDesc.write(ctx)  




class serClassDescValues(_abs_serBasicObject):
  _fields = ['_class_name']
  
  def setup_from_kwargs(self):
    self._class_name = self._kwargs['_class_name']
    # fix variable property list
    # possibly can handle that using orderedDict, tec
    for f in filter(lambda x:x[0]!='_' ,self._kwargs):
      self._fields.append(f)
  
  # -----8<------ 
    
  def write_obj(self, ctx):
    ## print(self._fields, "VS", self.__tmp)
    ctx.log_dbg(f"Will write : {self._fields}")
    for item in self._fields:
      if item.startswith('_'):
        ctx.log_dbg(f"SKIP: {item}")
        continue
      func_name = f"_write_item__{item}"
      func_ptr  = getattr(self, func_name)
      ctx.log_inf(f"WRITE {self._class_name}::{item}")
      func_ptr(ctx)
  
  def _write_item__externalContent(self, ctx):
    self.externalContent.write(ctx)
  
  def _write_item__serialdata(self, ctx):
    self.serialdata.write(ctx)
    
  def _write_item__objectAnnotation(self, ctx):
    self.objectAnnotation.write(ctx)
    
  # -----8<------  
  
  def read_obj(self, ctx):
    
    cdesc = self._kwargs.get('_cdesc', None)
    assert cdesc is not None, "Need _cdesc !"
  
    self._class_name = cdesc._get_name()
    ctx.reader.last_item().info = f"for class : {self._class_name}"
    
    
    if cdesc.TC == javaConst.TC_PROXYCLASSDESC:
      # nothing to read 
      return 
    
    fields = _classDescFlags_to_fields(cdesc.classDescFlags.value)
    self.__tmp = fields
    
    for item in fields:
      setattr(self, item, None)
      func_name = f"_read_item__{item}"
      func_ptr  = getattr(self, func_name)
      ctx.log_dbg(f"Reading classData [{item}] using [{func_name}]")
      #with ctx.scope(f"Reading values {self._class_name}::{item}"):
      ctx.reader.will_read(item)
      #with ctx.reader.start_list(item):
      func_ptr(ctx, cdesc)
      self._fields.append(item)
    

      
  def _read_item__externalContent(self, ctx, _):
    self.externalContent = read_blockdata_uintill_end(ctx, info='externalContent')

  def _read_item__objectAnnotation(self, ctx, _):
    self.objectAnnotation = read_objectAnnotation(ctx, info="objectAnnotation")
    
  def _read_item__serialdata(self, ctx, cdesc):
    self.serialdata = serListOfObj()
    with ctx.reader.start_list():
      for item in self._iter_read_fields_by_classDesc(ctx, cdesc):
        self.serialdata.append(item)

  def _iter_read_fields_by_classDesc(self, ctx, cdesc):
    cnt = len(cdesc.fields.value)
    if cnt == 0:
      ctx.log_dbg("Read values : ZERO fields to read ")
      return
    field_names = ' | '.join(a.fieldName.value for a in cdesc.fields)
    ctx.log_dbg(f"Reading fields : (count:{cnt}) [{field_names}]")
    for i,f in enumerate(cdesc.fields):
      ctx.log_dbg(f"read field {i+1} of {cnt} (`{self._class_name}::{f.fieldName.value}`)")
      ctx.log_dbg(f"-> Field type:{f.typecode}/{chr(f.typecode)} name:{f.fieldName.value}")
      item = _read_single_typecode_value(ctx, f.typecode)
      yield item
        


class serTC_OBJECT(_abs_serTCValue):
  TC = javaConst.TC_OBJECT
  _fields = ['classDesc','handle', 'classData']

  def read_obj(self, ctx):
 
    ctx.reader.will_read("classDesc")
    self.classDesc = read_classDesc(ctx)
    ctx.log_dbg(f"ClassDesc type : 0x{self.classDesc.TC:02x}/{_cname(self.classDesc)}")
      
    self.handle = serHandle(ctx=ctx, ref=self)
    
    #with ctx.scope(f"read classData(s) for {self.classDesc._get_name()}"):
    ctx.reader.will_read("classData")
    with ctx.reader.start_list():
      self.classData = serListOfObj()
      self.read_classData(ctx)
    
  def read_classData(self, ctx):  
    
    ctx.log_dbg("Get classDesc stack ... ")
    class_desc_stack = self._get_classDesc_stack()
    ctx.log_inf(f" classDesc count : {len(class_desc_stack)}")

    for cdesc in class_desc_stack[::-1]:
      ctx.log_dbg(f"values for {self.classDesc._get_name()}::{cdesc._get_name()}")
      #with ctx.scope(f"class values for {self.classDesc._get_name()}::{cdesc._get_name()} "):
      self.classData.append(
        serClassDescValues(ctx, _cdesc = cdesc)
      )   
  
  def _get_classDesc_stack(self):
    class_desc_stack = []
    cur = self.classDesc
    while cur.TC != javaConst.TC_NULL:
      class_desc_stack.append(cur)
      cur = cur.superClassDesc
    return class_desc_stack
      
  def write_obj(self, ctx):
    for key in self._fields:
      ctx.log_inf(f"WRITE ITEM: {key}")
      getattr(self, key).write(ctx)



    
    

  def get_simple_value(self):
    class_desc_stack  = self._get_classDesc_stack()[::-1]
    #master_classdesc = class_desc_stack.pop()
    class_value_stack = self.classData.value
    retval = []
    
    assert len(class_desc_stack) == len(class_value_stack), "Mismatch number of items !"
    for cdesc, cval in zip(class_desc_stack, class_value_stack):
      field_names = [ x.fieldName.value for x in cdesc.fields ][::-1]
      
      class_values = []
      for values_src in _classDescFlags_to_fields(cdesc.classDescFlags.value):
        vals = getattr(cval, values_src, None)
        for item in vals:        
          val = item.get_simple_value()
          if len(field_names) > 0:
            #class_values.append({"FIELD" : field_names.pop(), "VALUE" : val})
            class_values.append({field_names.pop() : val})
          else:
            class_values.append(val)
        
      #values = [ fields, field_names ]
      
      retval.append({
       "class" : { "name" : cdesc.className.value, "uid" : cdesc.UID.value },
       "values" : class_values,
      })
    return retval
  
  
  def old1(self):
    

    if self.classDesc .TC == javaConst.TC_CLASSDESC:
      class_name = master_classdesc.className.value
      uid = master_classdesc.UID.value
 
    values = []
    
    def _get_vals_of_collection(col):
      for item in col : # class_vals.objectAnnotation:
        values.append(item.get_simple_value())
    
    for class_vals in self.classData.value: # iterate over lsit of (sub)class values
      val_src = []
      if flags & javaConst.SC_SERIALIZABLE :
        val_src.append('serialdata')
      if flags & javaConst.SC_WRITE_METHOD :
        val_src.append('objectAnnotation')
      if flags & javaConst.SC_EXTERNALIZABLE:
        if flags & javaConst.SC_BLOCK_DATA:
          val_src.append('externalContent')
        else:
          val_src.append('objectAnnotation')
      #print(f"Getting values from {val_src}")
      for src_name in val_src:
        tmp = getattr(class_vals, src_name, None)
        if tmp is not None:
          _get_vals_of_collection(tmp)


    
    return {
      "Class" : {"Name":class_name, "UID":uid },
      "values" : values,
    }





def _read_single_typecode_value(ctx, tc):
  ctx.log_inf(f"Read item type {tc}/{chr(tc)} ...")
  if tc in javaConst.prim_typecode:
    return serValuePrimitive(ctx=ctx, _typecode_hint=tc)
    # that is ok ;)
  # else -> object || array  
  elif tc == javaConst.TYPECODE_OBJECT:
    ctx.log_dbg(" OBJECT VALUE !!! ")
    return read_object(ctx)
  elif tc == javaConst.TYPECODE_ARRAY:
    ctx.log_dbg(" ARRAY VALUE !!! ")
    #return read_newArray(ctx)
    return read_array(ctx) # array || ref || null
  else:
    assert tc, f"Bad TYPECODE = {tc}"

 

TYPECODE_TO_FORMAT = {
  'B' : ">b",
  'C' : '>b',
  'D' : '>d',
  'F' : ">f",
  'I' : ">i",
  'Z' : '>b',
  'J' : '>q',
  'S' : '>h',
}


class serValuePrimitive(_abs_serBasicObject): 
  # single value based on typecode 
  _fields = ['_typecode_hint', 'value']
  _format = None
  _typecode_hint = 'x'

  def init(self):
    self._typecode_hint = self._kwargs.get('_typecode_hint', None) # required arg !
    assert self._typecode_hint is not None, "Need _typecode_hint !!!"
    self._format = TYPECODE_TO_FORMAT[chr(self._typecode_hint)]

  def read_obj(self, ctx):
    ctx.log_inf(f"Read [{self._typecode_hint}] -> [{self._format}]")
    ctx.reader.will_read('value')
    self.value = ctx.wire.read_fmt(self._format)


  def write(self, ctx):
    ctx.wire.write_fmt(self._format, self.value)

  def get_simple_value(self):
    return f"(primitive:{self._format}) {self.value}"


class serTC_STRING(_abs_serTCValue):
  TC = javaConst.TC_STRING
  _fields = ['value']

  def read_obj(self, ctx):
    self.handle = serHandle(ctx=ctx, ref=self)
    ctx.reader.will_read("value")
    self.value = serJavaString(ctx=ctx)


  def write_obj(self, ctx):
    self.value.write(ctx)

  def get_simple_value(self):
    return f"(stringObject) {self.value.value}"



class serTC_LONGSTRING(_abs_serTCValue):
  TC = javaConst.TC_LONGSTRING

  def read_obj(self, ctx):
    self.handle = serHandle(ctx=ctx, ref=self)
    self.value = serJavaString(ctx=ctx)





class serTC_ARRAY(_abs_serTCValue):
  TC = javaConst.TC_ARRAY
  _fields = ['classDesc','handle','size','value']
  
  def read_obj(self, ctx):
    #classDesc newHandle (int)<size> values[size]
    ctx.reader.will_read("classDesc")
    self.classDesc = read_classDesc(ctx)
    
    self.handle = serHandle(ctx=ctx, ref=self)
    
    ctx.reader.will_read("size")
    self.size = ctx.wire.read_dword()
    ctx.log_dbg(f"Array size : {self.size}")
    
    ctx.reader.will_read("items")
    with ctx.reader.start_list():
      self._read_values(ctx)
    
    
    
  def _read_values(self, ctx):
    cdesc = self.classDesc 
    #ctx.resolve_if_needed(self.classDesc)
    # __getattr__ hack handles that 
    
    type_str = cdesc.className.value # TODO: FIX REFERECNCE !!!
    
    assert type_str[0] == '[', "WTF is that array !?"
    self.value = serListOfObj()
    class_name = cdesc.className.value
    typecode = ord(class_name[1])
    for i in range(self.size):
      ctx.log_dbg(f"Array item read {i} of {self.size} / {class_name}")
      item =  _read_single_typecode_value(ctx, typecode)  
      self.value.append(item)
    ### ctx.register_object(self.handle.v, self)

  def write_obj(self, ctx):
    self.classDesc.write(ctx)
    self.handle.write(ctx)
    # TODO: ctx.wire.write_dword() ... 
    self.value.write(ctx, include_size='>I')

  def get_simple_value(self):
    retval = []
    for item in self.value:
      retval.append(item.get_simple_value())
    return retval

class serTC_ENUM(_abs_serTCValue):
  TC = javaConst.TC_ENUM
  _fields = ['classDesc','handle','enumName']
  
  def read_obj(self, ctx):
    ctx.reader.will_read("class_description")
    self.classDesc = read_classDesc(ctx)
    self.handle = serHandle(ctx=ctx, ref=self)
    ctx.reader.will_read("enum_const_name")
    self.enumName = read_object(ctx)
    

  def write_obj(self, ctx):
    self.classDesc.write(ctx)
    self.handle.write(ctx)
    self.enumName.write(ctx)
    
    

class serTC_BLOCKDATA(_abs_serTCValue):
  TC = javaConst.TC_BLOCKDATA
  _fields = ['size','value']
  def read_obj(self, ctx):
    ctx.reader.will_read("size")
    self.size = ctx.wire.read_byte()

    ctx.reader.will_read("value")
    self.value = ctx.wire.read(self.size)

    ctx.log_dbg(f"BLOCKDATA ({self.size}) : {self.value}")

  def write_obj(self, ctx):
    ctx.wire.write_byte(self.size)
    ctx.wire.write(self.value)

  def to_dict(self):
    rv = dict(
      size = self.size ,
      data_hex = self.value.hex(),
      data_str = str(self.value) ,
    )
    return rv

  def get_simple_value(self):
    #return { "HEX": self.value.hex(), "STR":  str(self.value) }
    return { "BLOCKDATA":  str(self.value) }

    

class serTC_BLOCKDATALONG(_abs_serTCValue):
  TC = javaConst.TC_BLOCKDATALONG
  # TODO : implement
  
  

class serTC_REFERENCE(_abs_serTCValue):
  TC = javaConst.TC_REFERENCE
  _fields = ['handle']
  
  def read_obj(self, ctx):
    self._ref_ctx = ctx
    ctx.reader.will_read("handle")
    self.handle = ctx.wire.read_dword()
    ctx.log_inf(f"HandleRef : {self.handle:08x}")
  
  def write_obj(self, ctx):
    ctx.wire.write_dword(self.handle)
    
  ## HACKS TO ACCESS REFERENCES 

  def __getattr__(self, __name: str):
    self._ref_ctx.log_dbg(f"!! NOTICE: resolveing attr [{__name}] on reference 0x{self.handle:08x}")
    #raise Exception(f"You tried to get attr {__name} of TC_REFERENCE !")
    
    ref_obj = self._ref_ctx.get_ref(self.handle)
    ret_val = getattr(ref_obj, __name, None)
    
    
    
    if ret_val is None:
      self._ref_ctx.show_refs()
    #time.sleep(1)
    

    assert ret_val is not None, f"TC_REFERENCE [0x{self.handle:08X}] lookup `{__name}` returned NONE !"
    self._ref_ctx.log_dbg(f"!! SUCCESS lookup -> {__name} from { _cname(ref_obj)}")
    # time.sleep(1)
    return ret_val
    
  
    
    
 #self.raw += tmp
class serTC_ENDBLOCKDATA(_abs_serTCValue):
  TC = javaConst.TC_ENDBLOCKDATA
  _is_empty = True

class serTC_NULL(_abs_serTCValue):
  TC = javaConst.TC_NULL
  _is_empty = True
  
  def get_simple_value(self):
    return "<NULL>"
 
class serTC_EXCEPTION(_abs_serTCValue):
  TC = javaConst.TC_EXCEPTION
  _is_empty = True

class serTC_RESET(_abs_serTCValue):
  TC = javaConst.TC_RESET
  _is_empty = True











def read_fieldDesc(ctx):
  return try_read_stuff(
    ctx,
    frendly_name = "fieldDescrption",
    options = [
      read_primitiveDesc,
      read_objectDesc,
    ])


def read_classDesc(ctx):
  return try_read_stuff(
    ctx,
    "classDesc",
    options = [
      read_newClassDesc,    #  \__ newClassDescri or proxy
      read_proxyClassDesc , #  / 
      read_nullReference,
      read_prevObject,
    ])

def read_newClassDesc(ctx):
  return try_read_stuff(
    ctx,
    "newClassDesc",
    options = [
      serTC_CLASSDESC,
      serTC_PROXYCLASSDESC,
    ])
  
def read_superClassDesc(ctx):
  return read_classDesc(ctx)

def read_newClass(ctx):
  return serTC_CLASS( ctx=ctx )

def read_proxyClassDesc(ctx):
  return serTC_PROXYCLASSDESC( ctx=ctx )

def read_newArray(ctx):
  return serTC_ARRAY( ctx=ctx )

def read_array(ctx):
  return try_read_stuff(
    ctx,
    "array",
    options=[
      serTC_ARRAY,
      serTC_REFERENCE,
      serTC_NULL,
    ]
  )

def read_newString(ctx):
  return try_read_stuff(
    ctx,
    "newString",
    options = [
      serTC_STRING,
      serTC_LONGSTRING,
    ]
  )


def read_newEnum(ctx):
  return serTC_ENUM(ctx=ctx)

def read_prevObject(ctx):
  return serTC_REFERENCE(ctx=ctx)

def read_nullReference(ctx):
  return serTC_NULL(ctx=ctx)

def read_exception(ctx):
  return serTC_EXCEPTION(ctx=ctx)

def read_TC_RESET(ctx):
  return serTC_RESET(ctx=ctx)




def read_blockdata(ctx):
  return try_read_stuff(
    ctx,
    "newBlockData",
    options = [
      read_blockdatashort,
      read_blockdatalong,
    ]
  )

def read_blockdatashort(ctx):
  return serTC_BLOCKDATA(ctx=ctx)

def read_blockdatalong(ctx):
  return serTC_BLOCKDATALONG(ctx=ctx)

def read_endBlockData(ctx):
  return serTC_ENDBLOCKDATA(ctx=ctx)


def read_blockdata_uintill_end(ctx, info='?'):
  retval = serListOfObj()
  with ctx.reader.start_list():
    ctx.log_dbg(f"read contents untill endBlockData @{info}")
    while True:
      try:
        item = read_endBlockData(ctx)
        retval.append(item)
        ctx.log_dbg("EndBlockData reached")
        return retval
      except ReadCheckFailed:
        ctx.log_dbg("Not End-block-data")
      did_read = False
      item = None
      
      try:
        item = read_blockdata(ctx)
        retval.append(item)
        did_read = True
      except ReadCheckFailed:
        pass # not blockdata 
      
      try:
        item = read_object(ctx)
        retval.append(item)
        did_read = True
      except ReadCheckFailed:
        pass 
      
      assert did_read, "FAIL TO READ BLOCKDATA||OBJECT"



def read_classAnnotation(ctx, info="??"): # or object 
  ctx.log_inf("classAnnotation")
  return read_blockdata_uintill_end(ctx, info)
  
def read_objectAnnotation(ctx, info="?"):
  ctx.log_inf("objectAnnotation")
  return read_blockdata_uintill_end(ctx, info) 







def read_newObject(ctx): # just to follow specs
  return serTC_OBJECT( ctx=ctx )



def read_object(ctx):
  return try_read_stuff(
    ctx, 
    "read_object",
    [
    read_newObject,
    read_newClass,
    read_newArray,
    read_newString,
    read_newEnum,
    read_newClassDesc,
    read_prevObject,
    read_nullReference,
    read_exception,
    serTC_RESET,
  ]
  )


def read_content(ctx):
  return try_read_stuff(
    ctx = ctx, 
    frendly_name = "read_content",
    options = [
      read_object,
      read_blockdata,
    ],
  )

def read_contents(ctx):
  content = serListOfObj()
  while ctx.wire.bytes_available() > 1:
    content.append( read_content(ctx) )
  return content
  


def try_read_stuff(ctx:object, frendly_name:str, options:list):
  """
    Try to read next item using readers from <options>
  """
  #names = list(x.__name__ for x in options)
  count = len(options)
  ctx.log_dbg(f"TRY: {frendly_name} (candidates count:{count})")
  for i, fnc in enumerate(options):
    try:
      ctx.log_dbg(f"try read no:{i+1:2}/{count} -> Try func:{fnc.__name__}")
      val = fnc(ctx)
      ctx.log_dbg(f"++ GOOD: {fnc} ")
      return val
    except ReadCheckFailed as ex:
      ctx.log_dbg(f" -> FAIL: {fnc.__name__} (reason: {str(ex)})")
  raise ReadCheckFailed(f"Fail to read - out of options at {frendly_name}")






class JavaDeserek:
  
  handle_counter = 0
  
  _depth = 0
  _show_pos = True
  _log_stack = []
  _exception_raised = False
  
  _ref = {}
  _ref_backlog = {}
  
  _silent = False

  wire    : bytewirez.Wire = None
  reader  = None  
  
  def __init__(self):
    self._log_stack = []
    self._exception_raised = False
    self._ref = {}
    self._ref_backlog = {}


  def attach_wire(self, wire):
    self.wire = wire
    
  def next_handle_number(self):
    tmp = self.handle_counter 
    self.handle_counter += 1
    return tmp 

  def get_ref(self, ref_id):
    self.log_dbg(f"Get ref to {ref_id:08x}")
    self._ref_backlog[ref_id] += 1
    #time.sleep(1)
    return self._ref[ref_id]

  def register_object(self, ref_id, value):
    self.log_dbg(f"*** *** Register [0x{ref_id:04x}] = [{value.__class__}] *** ***")
    self._ref[ref_id] = value
    self._ref_backlog[ref_id] = 0
    #time.sleep(1)

  def show_refs(self): # debug mode
    print("### REFERENCE DUMP ### ")
    for k,v in self._ref.items():
      print(f"## {k:08x} => {_cname(v)}  # {self._ref_backlog[k]}")
      if v.TC == javaConst.TC_CLASSDESC:
        x = f"DESC_>NAME: {v.className.value}"
      # items w/ classDesc 
      elif v.TC in [javaConst.TC_OBJECT, javaConst.TC_ARRAY]: 
        if v.classDesc.TC == javaConst.TC_REFERENCE:
          x = f'REF : {v.classDesc.handle:08X}'
        else:
          x = f'OBJ->DESC->NAME: {v.classDesc.className.value}'
      elif v.TC == javaConst.TC_STRING:
        x = f"STR: {v.value.value}"
      else:
        raise Exception("WTF 3")
       
      print(f"## -> {x}")
    #time.sleep(2)



  def log_inf(self, msg):
    #self.reader.log_inf(msg)
    if not self._silent:
      logger.info(msg)

  def log_dbg(self, msg):
    #self.reader.log_dbg(msg)
    if not self._silent:
      logger.debug(msg)

  def log_war(self, msg):
    #self.reader.log_war(msg)
    if not self._silent:
      logger.warning(msg)




def do_serialize( stuff, skip_magic=False, silent=False):
  context = JavaDeserek()
  if silent:
    context._silent = True
  context.attach_wire( bytewirez.Wire(from_bytes=b'') )
  context.wire.set_endian(bytewirez.ENDIAN_BIG)
  
  if not skip_magic:
    context.wire.write(bytes.fromhex(javaConst.STREAM_MAGIC))
    context.wire.write_word(javaConst.STREAM_VERSION)
  
  stuff.write(context)

  return context.wire.dump()
  
   



def do_unserial(from_bytes=None, from_fd=None, **kw):
  if from_bytes:
    wire = bytewirez.Wire(from_bytes=from_bytes)
  elif from_fd:
    wire = bytewirez.Wire(from_fd = from_fd)
  else:
    raise Exception("No source provided")
  return _unserial_wire(
            wire = wire,
            **kw
          )




def _unserial_wire(
    wire, 
    silent = False, 
    save_struct_to = None, 
    save_format = None,
    showref = False
  ):
  
  context = JavaDeserek()

  wire.set_endian(bytewirez.ENDIAN_BIG)
  context.attach_wire(wire)
  context.reader = bytewirez.StructureReader(wire, logger = logger)
  #context.reader.logger = logger
  if silent:
    context._silent = True
    context.reader._silent = True
  
  with context.reader.start_object("DATA"):
    
    context.reader.will_read("magic")
    tmp = wire.readn(2)
    assert tmp == bytes.fromhex(javaConst.STREAM_MAGIC), f"Invalid MAGIC {tmp} != {javaConst.STREAM_MAGIC} "
    
    context.reader.will_read("version")
    tmp = wire.read_word() 
    assert tmp == javaConst.STREAM_VERSION, "Invalid VERSION"
    
    context.reader.will_read("contents")
    with context.reader.start_list():
      stuff = read_contents(context)
  
  if save_struct_to and save_format:
    f = open(save_struct_to,'w')
    if save_format == 'json':
      json.dump(context.reader.get_struct() , f)
    if save_format == 'imhex':
      f.write(context.reader.output_imHex())
  
  
  if showref:
    context.show_refs()

  return stuff



def simplyfy_object(j_obj):
  return j_obj.get_simple_value()





def _get_python_code_imports():
  return "\n".join([f"import {mod}" for mod in ["deserek", "javaConst"] ])
                    
                    



if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='JavaDeserializer')
  parser.add_argument('filename',   help='Load and parse file')
  parser.add_argument('--test',     help='Test stability of parsing', action="store_true", required=False)
  parser.add_argument("--format",   help="out format : yaml, json, python", required=False, default=None)
  parser.add_argument("--silent",   help="Silent mode", required=False, default=False, action="store_true")
  parser.add_argument("--showref",  help="Show reference table", required=False, default=False, action="store_true")
  parser.add_argument("--save-struct-to", help="Save binary structure pattern to FILENAME", default=None, required=False)
  parser.add_argument("--save-struct-fmt", help="Save binary structure pattern FORMAT (json==default|imhex|kaitai)", default="json", required=False)
  
  parser.add_argument(
    "--log-level",
    help = "set logLevel to value (info|debug|warning|error)",
    default="debug",
  )

  args = parser.parse_args()

  if args.silent:
    # SILENT MODE 
    logger.remove()


  
  bin1 = open(args.filename,"rb").read()
    
  if b'rO0' == bin1[:3] : 
    logger.warning("[HEURISTIC] Payload is base64 :)")
    bin1 = base64.b64decode(bin1)

  tmp = do_unserial(
    from_bytes = bin1, 
    silent = args.silent,
    save_struct_to = args.save_struct_to,
    save_format = args.save_struct_fmt,
    showref = args.showref
  )

  if not args.test:
    if args.format is None:
      print(" (no outpu format specified, but ... ) DONE !")
    elif args.format == 'yaml':
      print(yamlify(tmp))
    elif args.format == 'json':
      print(json.dumps(_dictify(tmp)))
    elif args.format == 'python':
      print(_get_python_code_imports())
      print("")
      print("obj = " + tmp.as_python())
      print("")
      print("if 1==1:")
      print(" import sys")
      print(" bin_data = deserek.do_serialize(obj)")
      print(" open(sys.argv[1],'wb').write(bin_data)")
    elif args.format == "simple":
        print( yaml.dump( simplyfy_object(tmp) , width=1000) )  
    else:
      raise Exception("Unknown output format !")
    
  else:    
    print(" > UNSERILIZED Succesfully !")
    print("*** TEST 1 : serialization : ")
    #time.sleep(2)    
    bin2 = do_serialize(tmp)

    print(f" ?? SERIALIZED :  LEN1={len(bin1)} , LEN2={len(bin2)} (saved as tmp2.bin/yml)")
    open("tmp2.bin","wb").write(bin2)
    open("tmp2.yml","w").write(yamlify(tmp))
    
    print(" ?? check if binary 1 & 2 format is identiacal ")
    assert bin1 == bin2, "Serialization 1-2 not stable"
    print(" ++ OK \n")


    #time.sleep(2)
    print("*** TEST 2 : Unserialize bin2 ")
    
    tmp3 = do_unserial(bin2)
    print(" ++ OK \n")
    
    print(" *** TEST 3 : serialization from python code ... ")
    #time.sleep(2)
    
    tmp4 = None
    MODULENAMEPREFIX = ''
    eval_str = 'tmp4 = {0}'.format( tmp.as_python() )
    
    open("tmp3.py","w").write(
      "import javaConst\nfrom deserek import *\n\n" + eval_str 
    )
    print(" -> Save do tmp3.py")
    exec(eval_str)
    
    print(" -> Serialize from tmp4 variable")
    bin4 = do_serialize(tmp4)
    print(f" ?? SERIALIZED :  LEN1={len(bin1)} , LEN2={len(bin4)} ")
    open("tmp4.bin","wb").write(bin4)
    open("tmp4.yml","w").write(yamlify(tmp))
    print(" ?? check if binary 1 & 4 format is identiacal ")
    assert bin1 == bin4, "Serialization 1-4 not stable"


    print("\n\nIf you see this message means that (de)serializator is stable !\n\n")


