from inspect import getmembers, signature
from typing import get_args
from rui.lib.rpc import RPC, RPCList

'''                             ''
    ~/.rpc-lists r/w interface
''                             '''

def get_rpclist(dev) -> RPCList:
    rpcs = rpc_dfs(dev.settings)
    return RPCList([node_to_rpc(rpc) for rpc in rpcs])

def node_to_rpc(node: "rpc") -> RPC:
    name = node.__name__
    call = node.__call__
    sig = signature(call)
    params, ret_type = sig.parameters, sig.return_annotation

    try:
        arg_type = params['arg'].annotation
        if arg_type == int | None: arg_type = int
        if arg_type == float | None: arg_type = float
        if arg_type == str | None: arg_type = str
    except KeyError:
        arg_type = None

    return RPC(name, call, arg_type, ret_type)

def is_rpc(x): return type(x).__name__.lower() == "rpc"
def is_survey(x): return type(x).__name__.lower() == "survey"
def rpc_dfs(parent) -> list["rpc"]:
    rpcs = []
    nodes = [v for a, v in getmembers(parent) if is_rpc(v) or is_survey(v)]
    for node in nodes:
        if is_rpc(node): rpcs += [node]
        rpcs += rpc_dfs(node)
    return rpcs
