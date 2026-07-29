import yaml 
from collections import OrderedDict


def _dictify(o):
  if getattr(o,'to_dict',None) is not None:
    return { str(type(o).__name__) : o.to_dict() }
  if type(o) is list:
    #print(o)
    #1/0
    return [_dictify(x) for x in o]
  #print(f"{o} NO JSON")
  return o # the value itself (should be primitive value)



yaml.add_representer(OrderedDict, lambda dumper, data: dumper.represent_mapping('tag:yaml.org,2002:map', data.items()))
def yamlify(o, width=1000):
  return yaml.dump(_dictify(o), default_flow_style=False,  width=width)





def _gen_required_py_imports():
  return '\n'.join( f"import {mod}" for mod in ["deserek", "javaConst"] )
  

def print_python_stub(unserialized_stuff):
  print(_gen_required_py_imports())
  print("")
  print("obj = " + unserialized_stuff.as_python())
  print("")
  print("if 1==1:")
  print(" import sys")
  print(" bin_data = deserek.do_serialize(obj)")
  print(" if len(sys.argv)>1:")
  print("  open(sys.argv[1],'wb').write(bin_data)")
  print(" else:")
  print("  sys.stdout.buffer.write(bin_data)")