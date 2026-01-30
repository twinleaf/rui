from inspect import signature, getmembers
from struct import error as StructError
from typing import Callable, TypeVar

from rpclib.tio import PROXY_ERROR, RPC_DNE_ERROR, RPC_TYPE_ERROR, BAD_REQ_ERROR
from rpclib.rpctypes import rpc_arg_type, rpc_ret_type
from rpclib.rpctypes import NAME_TO_TYPE, TYPE_NAME, TYPE_CAST, IS_ARG_TYPE

def process_request(dev, req: dict[str, str | rpc_arg_type ]) -> rpc_ret_type:
    ''' receives request from client tio.send_request, calls it, and replies with value '''
    # first check that we can do anything
    if not dev:
        return PROXY_ERROR

    # TODO: handle request errors & document error handling between daemon & client
    elif 'op' not in req: return "Malformed request: " + str(req)

    try:
        match req['op']:
            case 'rpc':
                return process_rpc(dev, req['name'], req['type'], req['arg'])
            case 'list':
                return process_rpc_list(dev)
            case 'is_sample':
                return process_is_sample(dev, req['name'])
            case 'get_sample':
                raise NotImplementedError # TODO: thread streams
            case 'itl':
                raise NotImplementedError # TODO: itl
            case _:
                return BAD_REQ_ERROR

    # KeyError if an attempt to read an arg from req failed
    except KeyError:
        return BAD_REQ_ERROR

def process_rpc(dev, name: str, type_name: str, arg: rpc_arg_type) -> rpc_ret_type:
    # find our rpc from string by traversing the survey tree
    rpc = dev.settings
    try:
        for survey in name.split('.'):
            rpc = getattr(rpc, survey)
    except AttributeError as e:
        return RPC_DNE_ERROR

    # call rpc with type conversion
    try:
        arg_type = NAME_TO_TYPE(type_name)
        arg = TYPE_CAST(arg, arg_type) # TODO: is this necessary??
        value = rpc() if arg is None else rpc(arg)

        if type(value) is float: value = round(value, 2)
        value = TYPE_CAST(value, str)
        assert value is not None
        return value
    except TypeError:
        return RPC_TYPE_ERROR
    except RuntimeError:
        return PROXY_ERROR

def process_rpc_list(dev) -> str: # TODO: what errors does this risk?
    names, nodes = member_dfs(dev.settings, "", lambda x: "urvey" not in str(type(x)))
    types = [TYPE_NAME(get_arg_type(node)) for node in nodes]
    return '\n'.join([n + '(' + t + ')' for n, t in zip(names, types)])

def process_is_sample(dev, name: str) -> bool:
    path = name.split('.')
    names_and_streams = [(s, v) for s, v in getmembers(dev.samples) if s[0] != '_']
    for name, stream in names_and_streams:
        parent = stream
        try:
            for p in path:
                parent = getattr(parent, p)
            return True # we got to the end, this is a child of stream
        except AttributeError:
            continue # this is not a sample in this stream

    return False # this is not a sample in any stream

def process_get_sample(dev, name: str) -> int | float: # TODO: what errors does this risk?
    for sample in dev._samples(n=1, columns=[name]):
        return sample[name]

'''                 ''
    daemon helpers
''                 '''

def get_arg_type(func: Callable) -> type | None:
    try:
        sig = signature(func)
        arg_type = sig.parameters['arg'].annotation

        # remove union
        if arg_type == int | None: arg_type = int
        if arg_type == float | None: arg_type = float
        if arg_type == type(None): arg_type = None # Not using NoneType
        #if arg_type == bytes: raise NotImplementedError("Don't know what to do with bytes yet")
    except KeyError:
        arg_type = None

    return arg_type

PT, LT = TypeVar("PT"), TypeVar("LT")
def member_dfs[PT, LT](parent: PT | LT, path: str,
               is_leaf: Callable[[PT | LT], bool]
               ) -> tuple[list[str], list[LT]]:
    ret_names, ret_nodes = [], []
    names_and_nodes = [(a, v) for a, v in getmembers(parent) if a[0] != '_']
    for name, node in names_and_nodes:
        if is_leaf(node):
            ret_names += [path + '.' + name]
            ret_nodes += [node]

        # rpcs can also have children
        new_path = name if path == '' else path + '.' + name
        new_names, new_nodes = member_dfs(node, new_path, is_leaf)
        ret_names += new_names
        ret_nodes += new_nodes
    return ret_names, ret_nodes
