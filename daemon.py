# TODO: organize this big ass file into a directory maybe
import os, sys, time, json, socket, threading
from inspect import signature, getmembers
from struct import error as StructError
from typing import Callable, TypeVar
import twinleaf

from rpclib.tio import SOCKET_PATH, PROXY_ERROR
from rpclib.tio import char_to_type, type_to_char
from rpclib.tio import RPC_DNE_ERROR, RPC_TYPE_ERROR

class RPCDaemon:
    '''Handles starting daemon, twinleaf.Device, & receiving client requests'''
    def __init__(self):
        self.dev_constructor = twinleaf.Device
        self.get_device()

    def get_device(self):
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
                client_thread = threading.Thread(target=self.handle_client, 
                                            args=(client,), daemon=True)
                client_thread.start()

    def handle_client(self, client: socket.socket):
        print("Got new client")
        with client:
            try:
                while True:
                    # receive, process, and reply
                    request = json.loads(client.recv(4096).decode())
                    reply = process_request(self.dev, request)
                    client.sendall( json.dumps({"rep": reply}).encode() )

                    # if we have a bad device, re-initalize it
                    if reply == PROXY_ERROR and self.dev is not None:
                        self.dev = None
                        reinit_thread = threading.Thread(target=self.get_device, args=())
                        reinit_thread.start()

            # bad request, this client is dead
            # TODO: what to do about ConnectionResetError?
            except json.decoder.JSONDecodeError:
                print("Client finished, waiting on new client")
                print()

from testdev import TestDevice
class TestDaemon(RPCDaemon):
    ''' Daemon with fake device object for testing '''
    def __init__(self):
        self.dev_constructor = TestDevice
        self.get_device()

'''                    ''
     daemon methods
''                    '''
def process_request(dev, req: dict[str, str]) -> str:
    ''' server receives request from client, calls it, and replies with value '''
    # first check that we can do anything
    if not dev: return PROXY_ERROR
    # TODO: handle request errors & document error handling between daemon & client
    elif 'op' not in req: return "Malformed request: " + str(req)
    match req['op']:
        case 'rpc':
            return process_rpc(dev, req)
        case 'list':
            return process_rpc_list(dev)
        case _:
            return "Unknown request: " + str(req)

def process_rpc(dev, req: dict[str, str]) -> str:
    req_name, req_type_char, req_arg = req['name'], req['type_char'], req['arg']

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
        req_type = char_to_type(req_type_char)
        arg = None if req_type is type(None) or arg is None else req_type(arg)
        value = rpc() if arg is None else rpc(arg)
        return str(value) if type(value) is not bytes else value.decode()
    except RuntimeError as e: 
        # rpc fails on proxy disconnect
        return PROXY_ERROR

def process_rpc_list(dev) -> str:
    names, nodes = member_dfs(dev.settings, "", lambda x: "urvey" not in str(type(x)))
    types = [type_to_char(get_arg_type(node)) for node in nodes]
    return '\n'.join([n + '(' + t + ')' for n, t in zip(names, types)])

'''                 ''
    daemon helpers
''                 '''

def get_arg_type(func: Callable) -> type:
    # we don't care about return type
    try:
        sig = signature(func)
        arg_type = sig.parameters['arg'].annotation

        # remove union
        if arg_type == int | None: arg_type = int
        if arg_type == float | None: arg_type = float
    except KeyError:
        arg_type = type(None)

    return arg_type

PT, LT = TypeVar("PT"), TypeVar("LT")
def member_dfs[PT, LT](parent: PT, path: str,
               is_leaf: Callable[[PT | LT], bool]
               ) -> tuple[list[str], list[LT]]:
    ret_names, ret_nodes = [], []
    names_and_nodes = [(a, v) for a, v in getmembers(parent) if not a.startswith("_")]
    for name, node in names_and_nodes:
        if is_leaf(node):
            ret_names += [path + '.' + name]
            ret_nodes += [node]
        else:
            new_path = name if path == '' else path + '.' + name
            new_names, new_nodes = member_dfs(node, new_path, is_leaf)
            ret_names += new_names
            ret_nodes += new_nodes
    return ret_names, ret_nodes

# TODO: move execution of daemon into separate script
if __name__ == "__main__":
    try: 
        if len(sys.argv) > 1 and sys.argv[1] == 'test':
            daemon: RPCDaemon = TestDaemon()
        else:
            daemon = RPCDaemon()
        while True: daemon.server_loop()
    except (EOFError, KeyboardInterrupt):
        print("Interrupted, exiting")
