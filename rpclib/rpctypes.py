from typing import Any

'''                          ''
    type processing helpers
''                          '''
# TODO: what to do with bytes rpcs
rpc_arg_type = int | float | None
rpc_ret_type = int | float | str # "OK" for rpcs that return None
rpc_any_type = int | float | str | None

def IS_ARG_TYPE(x: Any):
    t = x if type(x) is type or x is None else type(x)
    return t in {int, float, None}
def IS_RET_TYPE(x: Any):
    t = x if type(x) is type else type(x)
    return t in {int, float, str}

# TODO: add typeerrors to people who use this, or wrap this in typeerror handler
TYPES_DICT = {'f': float, 'i': int,
              'u': int,  # unsigned ints from shell list
              's': None, # string in shell list means None -> str
              ')': None, # () in shell list means None -> None
              'N': None  # for python list, None.__name__
             }

def TYPE_NAME(t: type | None) -> str:
    if t is None: return ''
    else: return t.__name__

def TYPE_CAST(x: Any, t: type | None) -> rpc_any_type:
    if x is None: return None
    if t is None: return None
    if type(x) is bytes: x = x.decode()
    return t(x)
