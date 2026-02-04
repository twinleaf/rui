import os, sys, time, json, socket, subprocess
from rpclib.rpclib import rpc_arg_type, rpc_ret_type
from rpclib.rpclib import IS_ARG_TYPE, IS_RET_TYPE, TYPE_NAME
from rpclib.rpclib import SOCKET_PATH, PROXY_ERROR, RPC_DNE_ERROR, RPC_TYPE_ERROR, BAD_REQ_ERROR
from client.lib.tio_tool import tio_tool_rpc
from daemon.main import spawn_thread_daemon

class ProxyError(Exception): pass
class DaemonError(Exception): pass
RequestError = (TypeError, AssertionError)

'''                          ''
    choose daemon or shell
''                          '''
def daemon_shell_rpc(name: str, arg_type: type | None, arg: rpc_arg_type) -> rpc_ret_type:
    ''' framework to try daemon first, then shell. only this method can sys.exit '''
    # TODO: better error handling of different things that can happen with daemon/shell
    # For example, difference between a daemon runtime error and a shell runtime error?
    try:
        return daemon_rpc(name, arg_type, arg)
    except FileNotFoundError:
        process = spawn_thread_daemon(['--silent'])
        print("Trying to start daemon, using tio-tool for now")
    except ConnectionRefusedError:
        print("Proxy hasn't found device, trying tio-tool")
    except DaemonError:
        print("Error in daemon loop, trying tio-tool")
    except ProxyError:
        print("Error with daemon's proxy, trying tio-tool")
    # TODO: ConnectionResetError?
    except RequestError:
        sys.exit("Bad types on request data, exiting")

    # only get here if error
    try:
        return tio_tool_rpc(name, arg_type, arg)
    except FileNotFoundError:
        sys.exit("No tio-tool found, try installing or adding to PATH")
    except NotImplementedError as e:
        sys.exit(str(e))

'''                      ''
     daemon interface
''                      '''

def daemon_rpc(name: str, arg_type: type | None, arg: rpc_arg_type) -> rpc_ret_type:
    value = send_request({'op': 'rpc', 'name': name, 'type': TYPE_NAME(arg_type), 'arg': arg})
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
            raise DaemonError

        value = reply["rep"]

        if value == PROXY_ERROR: raise ProxyError
        if value == RPC_DNE_ERROR: raise RuntimeError
        if value == RPC_TYPE_ERROR: raise TypeError
        if value == BAD_REQ_ERROR: raise TypeError
        else: return value
