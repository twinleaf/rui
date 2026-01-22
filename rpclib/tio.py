import os, sys, subprocess
from typing import Callable, TypeVar
from struct import error as StructError

'''                          ''
    choose daemon or shell
''                          '''
RT = TypeVar("RT")
def daemon_shell(daemon: Callable[[], RT], shell: Callable[[], RT]) -> RT:
    ''' framework to try daemon first, then shell '''
    try:
        return daemon()
    except (ConnectionRefusedError, FileNotFoundError):
        # TODO: background daemon yourself
        print("\nDaemon not found, try starting it?")
    except DaemonError:
        print("\nError in daemon loop, trying shell")
    except ProxyError:
        print("\nError with daemon's proxy, defaulting to shell")

    # only get here if error
    try:
        return shell()
    except RuntimeError:
        print("Shell failed too, giving up")
        sys.exit()

def daemon_shell_rpc(name: str, arg_type: type, arg: str | None) -> str:
    type_char = type_to_char(arg_type)
    return daemon_shell(lambda: daemon_rpc(name, type_char, arg), 
                        lambda: shell_rpc(name, arg))

def daemon_shell_list() -> list[str]:
    return daemon_shell(lambda: daemon_rpc_list(),
                        lambda: [l.split()[1] for l in tio_tool("rpc-list").splitlines()])

'''                      ''
    rust tool interface
''                      '''
# TODO: make test shell interface

def shell_rpc(name: str, arg: str | None) -> str:
    result = tio_tool('rpc', name, arg)
    lines = result.splitlines()
    filtered = '\n'.join([l for l in lines if l.split()[0] not in {'Unknown', 'OK'}])
    return filtered

def tio_tool(tool: str, *args: str | None) -> str:
    argv = ['tio-tool', tool, '--'] + [a for a in args if a is not None]
    try: 
        output = subprocess.run(argv, capture_output=True)
        result = output.stdout.strip().decode(), output.stderr.strip().decode()
    except FileNotFoundError: 
        sys.exit("tio-tool not found, install or check PATH") 
    except TypeError: # for some reason it throws this on tio-tool fail sometimes
        print("tio-tool failed")
        raise RuntimeError

    if result[1]: 
        raise RuntimeError('\n'.join(result)) # stderr
    else: 
        return result[0] # stdout

'''                      ''
     daemon interface
''                      '''
# TODO: Connect in main script intead of in each rpc call
import json, socket

SOCKET_PATH = "/tmp/daemon.sock"
PROXY_ERROR = "Proxy failed, trying to restart..."
RPC_DNE_ERROR = "RPC does not exist"
RPC_TYPE_ERROR = "RPC failed, check type"
class ProxyError(Exception): pass
DaemonError = json.decoder.JSONDecodeError

# TODO: Better error handling
def send_request(req: dict[str, str | None]) -> str:
    ''' client sends request to server, reads back reply '''
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.connect(SOCKET_PATH)

        # request and reply
        request = json.dumps(req)
        client.sendall(request.encode())
        reply = json.loads(client.recv(4096).decode())
        value = reply["rep"]

        # proxy error tells us to try shell execution and re-init daemon device
        if value == PROXY_ERROR: raise ProxyError

        # other errors just bounce
        if value == RPC_DNE_ERROR: raise RuntimeError
        if value == RPC_TYPE_ERROR: raise TypeError(RPC_TYPE_ERROR)
        else: return value

def daemon_rpc(name: str, type_char: str, arg: str | None) -> str:
    value = send_request({'op': 'rpc', 'name': name, 'type_char': type_char, 'arg': arg})
    return f"Reply: {value}"

def daemon_rpc_list() -> list[str]:
    value = send_request({'op': 'list'})
    return value.splitlines()

'''                          ''
    type processing helpers
''                          '''
TYPE_ERROR = lambda x: f"Unknown data type: {x}"
TYPES_DICT = {'f': float, 'u': int, 'i': int, 's': type(None), ')': type(None), '': type(None)}
# TODO: skip bytes rpcs
CHARS_DICT = {float: 'f', int: 'i', bytes: '', str: 's', type(None): ''}

def char_to_type(char: str) -> type:
    try:
        return TYPES_DICT[char] 
    except KeyError: 
        raise TypeError(TYPE_ERROR(char))

def type_to_char(t: type) -> str:
    try:
        return CHARS_DICT[t]
    except KeyError:
        raise TypeError(TYPE_ERROR(t))

def char_to_typecast(char: str): # -> Callable[[Any], t | None]:
    t = char_to_type(char)
    if t is None: 
        return lambda x: None
    else:
        return lambda x: t(x) if x is not None else None
