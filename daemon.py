import os, sys, time, json, socket, threading
from struct import error as StructError
from inspect import getfullargspec
from typing import get_args, Callable, TypeVar

from testdev import TestDevice
from lib.tio import SOCKET_PATH, PROXY_ERROR
import twinleaf

class RPCDaemon:
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
        try:
            while True:
                request = json.loads(client.recv(4096).decode())
                reply = self.process_request(request)
                client.sendall( json.dumps({"rep": reply}).encode() )
                if reply == PROXY_ERROR:
                    if self.dev:
                        self.dev = None
                        reinit_thread = threading.Thread(target=self.get_device, args=())
                        reinit_thread.start()
        except json.decoder.JSONDecodeError as e:
            print("Client finished, waiting on new client")
            print()
        finally:
            client.close()  # close the connection

    def process_request(self, req: dict[str, str]) -> str:
        if 'op' not in req: return "Malformed request"
        if req['op'] != 'rpc': return "Unknown request"
        if not self.dev: return PROXY_ERROR
        req_name, req_arg = req['name'], req['arg']
        print(req_name, req_arg)

        # find our rpc from string by traversing the survey tree
        rpc = self.dev.settings
        try:
            for survey in req_name.split('.'): 
                rpc = getattr(rpc, survey)
            arg = cast_arg(rpc, req_arg) 
            value = rpc() if arg is None else rpc(arg)
            value = value.decode() if type(value) is bytes else str(value)
            return value
        except AttributeError as e: # getattr fails on nonexistent RPC
            return "RPC does not exist"
        except (ValueError, StructError) as e: # type conversion error
            return "Couldn't interpret argument, wrong type?"
        except RuntimeError as e: # rpc fails on proxy disconnect
            return PROXY_ERROR

class TestDaemon(RPCDaemon):
    def __init__(self):
        self.dev_constructor = TestDevice
        self.get_device()

RT = TypeVar("RT")
def cast_arg(func: Callable[[RT | None], RT], arg: str | None) -> RT | None:
    # cast arg to the input type of func
    if arg is None: return None
    spec = getfullargspec(func)
    annotations = spec.annotations
    if 'arg' in annotations:
        union = get_args(annotations['arg'])
        for t in union:
            if t is not type(None):
                arg = t(arg)
    return None

if __name__ == "__main__":
    try: 
        if len(sys.argv) > 1 and sys.argv[1] == 'test':
            daemon = TestDaemon()
        else:
            daemon = RPCDaemon()
        while True: daemon.server_loop()
    except (EOFError, KeyboardInterrupt):
        print("Interrupted, exiting")
