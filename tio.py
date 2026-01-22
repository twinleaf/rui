import os, sys, subprocess
from typing import Any

'''                      ''
    rust tool interface
''                      '''
# TODO: make test shell interface

def shell_rpc(name: str, arg: str | None) -> str:
    result = tio_tool('rpc', name, arg)
    lines = result.splitlines()
    filtered = '\n'.join([l for l in lines if l.split()[0] not in {'Unknown', 'OK'}])
    return filtered

def tio_tool(tool: str, *args: Any) -> str:
    argv = ['tio-tool', tool, '--'] + [str(arg) for arg in args if arg is not None]
    try: 
        output = subprocess.run(argv, capture_output=True)
        result = __parse_result(output.stdout), __parse_result(output.stderr)
    except FileNotFoundError: 
        sys.exit("tio-tool not found, install or check PATH") 

    if result[1]: 
        raise RuntimeError('\n'.join(result)) # stderr
    else: 
        return result[0] # stdout

def __parse_result(result: bytes) -> str:
    return result.strip().decode('utf-8')

'''                      ''
     daemon interface
''                      '''
# TODO: make test daemon interface
import json, socket

SOCKET_PATH = "/tmp/daemon.sock"
PROXY_ERROR = "Proxy failed, trying to restart..."
class ProxyError(Exception): pass
DaemonError = json.decoder.JSONDecodeError

def daemon_rpc(name: str, arg: str | None) -> str:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.connect(SOCKET_PATH)

        # TODO: send type instead of interpreting it since we have it
        request = json.dumps({'op': 'rpc', 'name': name, 'arg': arg})
        client.sendall(request.encode())
        reply = json.loads(client.recv(4096).decode())
        value = str(reply["rep"])
        if value == PROXY_ERROR: raise ProxyError
        else: return f"Reply: {value}"
