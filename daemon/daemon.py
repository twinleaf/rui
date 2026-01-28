# TODO: organize this big ass file into a directory maybe
import os, sys, time, json, socket, threading
from inspect import signature, getmembers
from struct import error as StructError
from typing import Callable, TypeVar

from rpclib.tio import SOCKET_PATH, PROXY_ERROR
from rpclib.tio import RPC_DNE_ERROR, RPC_TYPE_ERROR
from rpclib.rpctypes import rpc_arg_type, rpc_ret_type
from rpclib.rpctypes import NAME_TO_TYPE, TYPE_NAME, TYPE_CAST, IS_ARG_TYPE

class RPCDaemon:
    '''Handles starting daemon, twinleaf.Device, & receiving client requests'''
    def __init__(self, dev_constructor):
        self.dev_constructor = dev_constructor
        while True:
            try:
                print("Looking for device...")
                self.dev = self.dev_constructor()
                print(f"Got device {self.dev.settings.dev.name().decode()}")
                return
            except RuntimeError:
                self.dev = None
                print("Device not found, trying again in 5s...")
                time.sleep(5)

    def server_loop(self):
        if os.path.exists(SOCKET_PATH): os.remove(SOCKET_PATH)

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            server.bind(SOCKET_PATH)
            server.listen(5)
            print("Started server")

            while True:
                client, _ = server.accept()
                client_thread = threading.Thread(target=self._handle_client, 
                                            args=(client,), daemon=True)
                client_thread.start()

    def _handle_client(self, client: socket.socket):
        with client:
            try:
                while True:
                    # receive, process, and reply
                    request = json.loads(client.recv(8192).decode())
                    reply = process_request(self.dev, request)
                    client.sendall( json.dumps({"rep": reply}).encode() )

                    # if we have a bad device, re-initalize it
                    if reply == PROXY_ERROR and self.dev is not None:
                        self.dev = None
                        reinit_thread = threading.Thread(target=self.__init__, args=())
                        reinit_thread.start()

            except ConnectionResetError:
                print("Client's recv not big enough for server request, failed")
                return
            except json.decoder.JSONDecodeError:
                # couldn't receive anything, we're done
                return

'''                    ''
     daemon methods
''                    '''
def process_request(dev, req: dict[str, str | rpc_arg_type ]) -> rpc_ret_type:
    ''' receives request from client tio.send_request, calls it, and replies with value '''
    # first check that we can do anything
    if not dev: return PROXY_ERROR
    # TODO: handle request errors & document error handling between daemon & client
    elif 'op' not in req: return "Malformed request: " + str(req)
    match req['op']:
        case 'rpc':
            return process_rpc(dev, req)
        case 'list':
            return process_rpc_list(dev)
        case 'itl':
            raise NotImplementedError # TODO: itl
        case _:
            return "Unknown request: " + str(req)

def process_rpc(dev, req: dict[str, str | rpc_arg_type]) -> rpc_ret_type:
    req_name, req_type_name, req_arg = req['name'], req['type'], req['arg']
    assert type(req_name) is str
    assert type(req_type_name) is str
    assert IS_ARG_TYPE(req_arg)

    # find our rpc from string by traversing the survey tree
    rpc = dev.settings
    try:
        for survey in req_name.split('.'):
            rpc = getattr(rpc, survey)
    except AttributeError as e: 
        # getattr fails on nonexistent RPC
        return RPC_DNE_ERROR

    # call rpc with type conversion
    try:
        req_type = NAME_TO_TYPE(req_type_name)
        arg = TYPE_CAST(req_arg, req_type)
        value = rpc() if arg is None else rpc(arg)
        value = TYPE_CAST(value, str)
        assert value is not None
        return value
    except TypeError:
        return RPC_TYPE_ERROR
    except RuntimeError:
        # rpc fails on proxy disconnect
        return PROXY_ERROR

def process_rpc_list(dev) -> str:
    names, nodes = member_dfs(dev.settings, "", lambda x: "urvey" not in str(type(x)))
    types = [TYPE_NAME(get_arg_type(node)) for node in nodes]
    return '\n'.join([n + '(' + t + ')' for n, t in zip(names, types)])

'''                 ''
    daemon helpers
''                 '''

def get_arg_type(func: Callable) -> type | None:
    # we don't care about return type
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
    names_and_nodes = [(a, v) for a, v in getmembers(parent) if not a.startswith("_")]
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
