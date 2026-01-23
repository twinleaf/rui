import os, sys, subprocess
from typing import Callable, TypeVar, Any
from .rpctypes import rpc_arg_type, rpc_ret_type
from .rpctypes import IS_ARG_TYPE, IS_RET_TYPE, TYPE_NAME

'''                          ''
    choose daemon or shell
''                          '''
# TODO: Force daemon rpc-list
# If daemon not found, start it and make list
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

def daemon_shell_rpc(name: str, arg_type: type | None, arg: rpc_arg_type) -> rpc_ret_type:
    return daemon_shell(lambda: daemon_rpc(name, arg_type, arg), 
                        lambda: shell_rpc(name, arg_type, arg))

def daemon_shell_list() -> list[str]:
    return daemon_shell(lambda: daemon_rpc_list(),
                        lambda: [l.split()[1] for l in tio_tool("rpc-list").splitlines()])

'''                      ''
    rust tool interface
''                      '''
# TODO: make test shell interface
# TODO: get rid of shell rpc-list and merge these two funcs

def shell_rpc(name: str, arg_type: type | None, arg: rpc_arg_type) -> rpc_ret_type:
    result = tio_tool('rpc', name, str(arg))
    for line in result.splitlines():
        words = line.split()
        match words[0]:
            case 'Reply:':
                reply = words[1]
                if reply[0] == '"': reply = reply[1:-1] # trim quotes
                if arg_type is not None: reply = arg_type(reply)
                return reply
            case 'Unknown': # assuming string since no -T/-t, 
                continue
            case 'OK': # if this is all we get, we'll go to the return 'OK' at the end
                continue
            case 'RPC':
                if words[1] == 'failed':
                    raise RuntimeError(line)
                else:
                    raise NotImplementedError("Don't know what to do with " + line)
            case 'FAILED':
                raise RuntimeError(line)
            case _:
                raise NotImplementedError("Don't know what to do with " + line)
    return 'OK'

def tio_tool(tool: str, *args: str | None) -> str:
    argv = ['tio-tool', tool, '--'] + [a for a in args if a is not None and a != 'None']
    try: 
        output = subprocess.run(argv, capture_output=True)
        result = output.stdout.strip().decode(), output.stderr.strip().decode()
    except FileNotFoundError: 
        sys.exit("tio-tool not found, install or check PATH") 
    except TypeError: # for some reason it throws this on tio-tool fail sometimes
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

def daemon_rpc(name: str, arg_type: type | None, arg: rpc_arg_type) -> rpc_ret_type:
    assert IS_ARG_TYPE(arg)
    value = send_request({'op': 'rpc', 'name': name, 'type': TYPE_NAME(arg_type), 'arg': arg})
    assert IS_RET_TYPE(value)
    return value

def daemon_rpc_list() -> list[str]:
    value = send_request({'op': 'list'})
    assert type(value) is str
    return value.splitlines()

# TODO: Better error handling
def send_request(req: dict[str, str | rpc_arg_type]) -> rpc_ret_type:
    ''' sends request to daemon, reads back reply from daemon.process_request '''
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.connect(SOCKET_PATH)

        # request and reply
        request = json.dumps(req)
        client.sendall(request.encode())
        # TODO: handle not big enough error
        reply = json.loads(client.recv(4096).decode())
        value = reply["rep"]

        # proxy error tells us to try shell execution and re-init daemon device
        if value == PROXY_ERROR: raise ProxyError

        # other errors should just bounce
        if value == RPC_DNE_ERROR: raise RuntimeError
        if value == RPC_TYPE_ERROR: raise TypeError(RPC_TYPE_ERROR)
        else: return value
