import os, sys, json, socket, subprocess
from typing import Callable, TypeVar, Any
from .rpctypes import rpc_arg_type, rpc_ret_type
from .rpctypes import IS_ARG_TYPE, IS_RET_TYPE, TYPE_NAME

class ProxyError(Exception): pass
DaemonError = json.decoder.JSONDecodeError
RequestError = (TypeError, AssertionError)

'''                          ''
    choose daemon or shell
''                          '''
def daemon_shell_rpc(name: str, arg_type: type | None, arg: rpc_arg_type) -> rpc_ret_type:
    ''' framework to try daemon first, then shell. only this method can sys.exit '''
    try:
        return daemon_rpc(name, arg_type, arg)
    except (ConnectionRefusedError, FileNotFoundError):
        process = spawn_permanent_daemon()
        print("Starting daemon, using shell for now")
    except DaemonError:
        print("Error in daemon loop, trying shell")
    except ProxyError:
        print("Error with daemon's proxy, defaulting to shell")
    except RequestError:
        sys.exit("\nBad types on request data, exiting")

    # only get here if error
    try:
        return shell_rpc(name, arg_type, arg)
    except FileNotFoundError:
        sys.exit("No tio-tool found, try installing or adding to PATH")
    except NotImplementedError as e:
        sys.exit(str(e))
    # RuntimeError caught upstream TODO: is this true??

'''                      ''
     daemon interface
''                      '''
SOCKET_PATH = "/tmp/daemon.sock"
PROXY_ERROR = "Proxy failed, trying to restart..."
RPC_DNE_ERROR = "RPC does not exist"
RPC_TYPE_ERROR = "RPC failed, check type"
BAD_REQ_ERROR = "Malformed or unknown request"

def daemon_rpc(name: str, arg_type: type | None, arg: rpc_arg_type) -> rpc_ret_type:
    assert IS_ARG_TYPE(arg)
    value = send_request({'op': 'rpc', 'name': name, 'type': TYPE_NAME(arg_type), 'arg': arg})
    assert IS_RET_TYPE(value)
    return value

def daemon_check_is_sample(name) -> bool:
    try:
        return send_request({'op': 'is_sample', 'name': name})
    except FileNotFoundError:
        # No daemon to check, must assume the worst
        return True

def send_request(req: dict[str, str | rpc_arg_type]) -> rpc_ret_type:
    ''' sends request to daemon, reads back reply from daemon.process_request '''
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.connect(SOCKET_PATH)

        # request and reply
        request = json.dumps(req)
        client.sendall(request.encode())
        try:
            reply = json.loads(client.recv(8192).decode())
        except json.decoder.JSONDecodeError:
            raise ProxyError
        except ConnectionResetError:
            raise ProxyError
        value = reply["rep"]

        if value == PROXY_ERROR: raise ProxyError
        if value == RPC_DNE_ERROR: raise RuntimeError
        if value == RPC_TYPE_ERROR: raise TypeError(RPC_TYPE_ERROR)
        else: return value

def spawn_permanent_daemon() -> subprocess.Popen:
    findrpc_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    findrpc_script = os.path.join(findrpc_dir, 'findrpc.py')

    with open(os.devnull, 'w') as devnull:
        process = subprocess.Popen(
            [sys.executable, findrpc_script, "daemon", "--silent"],
            stdout=devnull, stderr=devnull, 
            close_fds=True, start_new_session=True)
    return process

'''                      ''
    rust tool interface
''                      '''
# TODO: make test shell interface
def shell_rpc(name: str, arg_type: type | None, arg: rpc_arg_type) -> rpc_ret_type:
    try:
        argv = ['tio-tool', 'rpc', '--']
        argv.append(name)
        if arg is not None: argv.append(str(arg)) # only here do we convert to str

        process = subprocess.Popen(argv, stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

    except TypeError: # for some reason it throws this on tio-tool fail sometimes
        raise RuntimeError("tio-tool failure") # catch this error upstream

    if stderr:
        raise RuntimeError(stderr.strip())

    result = stdout.strip()
    for line in result.splitlines():
        words = line.split()
        match words[0]:
            case 'Reply:':
                reply = words[1]
                if reply[0] == '"': reply = reply[1:-1] # trim quotes
                # convert manually here; ret type might be non-None even if arg type None
                if arg_type is not None: reply = arg_type(reply)
                return reply
            case 'Unknown': # assuming string since no -T/-t
                continue
            case 'OK': # if this is all we get, we'll go to the return 'OK' at the end
                continue
            case 'RPC': # should be "RPC failed: [reason]"
                raise RuntimeError(name + ' | ' + line)
            case _:
                raise NotImplementedError("Don't know what to do with " + line)
    return 'OK'
