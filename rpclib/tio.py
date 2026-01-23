import sys, json, socket, subprocess
from typing import Callable, TypeVar, Any
from .rpctypes import rpc_arg_type, rpc_ret_type
from .rpctypes import IS_ARG_TYPE, IS_RET_TYPE, TYPE_NAME

'''                          ''
    choose daemon or shell
''                          '''
# TODO: Force daemon rpc-list
# If daemon not found, start it and make list
def daemon_shell_rpc(name: str, arg_type: type | None, arg: rpc_arg_type) -> rpc_ret_type:
    ''' framework to try daemon first, then shell '''
    try:
        return daemon_rpc(name, arg_type, arg)
    except (ConnectionRefusedError, FileNotFoundError):
        # TODO: background daemon yourself
        print("\nDaemon not found, try starting it?")
    except DaemonError:
        print("\nError in daemon loop, trying shell")
    except ProxyError:
        print("\nError with daemon's proxy, defaulting to shell")

    # only get here if error
    return shell_rpc(name, arg_type, arg)

'''                      ''
    rust tool interface
''                      '''
# TODO: make test shell interface
def shell_rpc(name: str, arg_type: type | None, arg: rpc_arg_type) -> rpc_ret_type:
    try:
        argv = ['tio-tool', 'rpc', '--']
        argv.append(name)
        if arg is not None: argv.append(str(arg)) # only here do we convert to str
        output = subprocess.run(argv, capture_output=True)
    except FileNotFoundError: 
        sys.exit("tio-tool not found, install or check PATH") 
    except TypeError: # for some reason it throws this on tio-tool fail sometimes
        raise RuntimeError # catch this error upstream

    result = output.stdout.strip().decode()
    for line in result.splitlines():
        words = line.split()
        match words[0]:
            case 'Reply:':
                reply = words[1]
                if reply[0] == '"': reply = reply[1:-1] # trim quotes
                # convert manually here; ret type might be non-None even if arg type None
                if arg_type is not None: reply = arg_type(reply)
                return reply
            case 'Unknown': # assuming string since no -T/-t, 
                continue
            case 'OK': # if this is all we get, we'll go to the return 'OK' at the end
                continue
            case 'FAILED' | 'RPC': # should be "RPC failed: [reason]"
                raise RuntimeError(line)
            case _:
                raise NotImplementedError("Don't know what to do with " + line)
    return 'OK'

'''                      ''
     daemon interface
''                      '''
# TODO: Connect in main script intead of in each rpc call

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

# TODO: Better error handling
def send_request(req: dict[str, str | rpc_arg_type]) -> rpc_ret_type:
    ''' sends request to daemon, reads back reply from daemon.process_request '''
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.connect(SOCKET_PATH)

        # request and reply
        request = json.dumps(req)
        client.sendall(request.encode())
        # TODO: handle not big enough error
        reply = json.loads(client.recv(8192).decode())
        value = reply["rep"]

        # proxy error tells us to try shell execution and re-init daemon device
        if value == PROXY_ERROR: raise ProxyError

        # other errors should just bounce
        if value == RPC_DNE_ERROR: raise RuntimeError
        if value == RPC_TYPE_ERROR: raise TypeError(RPC_TYPE_ERROR)
        else: return value
