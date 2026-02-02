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

TYPES_DICT = {'float': float, 'int': int,
              'bytes': None, # bytes will be None for now as well
              'str': None, # string in shell list means None -> str
              '':  None  # () as well
             }
def NAME_TO_TYPE(name: str) -> type | None:
    try:
        return TYPES_DICT[name]
    except KeyError:
        raise TypeError

def TYPE_NAME(t: type | None) -> str:
    if t is None: return ''
    else: return t.__name__

def TYPE_CAST(x: Any, t: type | None) -> rpc_any_type:
    if x is None: return None
    if t is None: return None
    if type(x) is bytes: x = x.decode()
    try:
        return t(x)
    except ValueError:
        raise TypeError

'''                 ''
    TIO constants
''                 '''

class ProxyError(Exception): pass

SOCKET_PATH = "/tmp/daemon.sock"
PROXY_ERROR = "Proxy failed, trying to restart..."
RPC_DNE_ERROR = "RPC does not exist"
RPC_TYPE_ERROR = "RPC failed, check type"
BAD_REQ_ERROR = "Malformed or unknown request"
