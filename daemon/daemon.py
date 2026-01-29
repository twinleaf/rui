import os, time, json, socket, threading
from rpclib.tio import SOCKET_PATH, PROXY_ERROR
from .process import process_request

class RPCDaemon:
    '''Handles starting daemon, twinleaf.Device, & receiving client requests'''
    def __init__(self, dev_constructor, server_override=False):
        self.dev_constructor = dev_constructor
        self.server_override = server_override
        self.socket_available = False
        self.dev = None

    def __enter__(self):
        self.socket_available = not os.path.exists(SOCKET_PATH)

        # If override, we can't kill the old server but we can usurp its socket
        if self.server_override and not self.socket_available:
            os.remove(SOCKET_PATH)
            self.socket_available = True

        return self

    def get_device(self):
        # If we have a socket, look for a device
        # If not, server_loop will raise OSError and go to __exit__
        while self.socket_available:
            try:
                print("Looking for device...")
                self.dev = self.dev_constructor()
                print(f"Got device {self.dev.settings.dev.name().decode()}")
                break # go to return

            # dev_constructor will raise this if no device
            except RuntimeError:
                self.dev = None
                print("Device not found, trying again in 5s...")
                time.sleep(5)

    def server_loop(self):
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.bind(SOCKET_PATH) # raise OSError if socket in use
        self.server.listen(5) # accept up to five clients (arbitrary)
        print("Started server")

        while True:
            assert self.still_connected()
            client, _ = self.server.accept() # block here until client arrives
            client_thread = threading.Thread(target=self._handle_client,
                                        args=(client,), daemon=True)
            client_thread.start()

    def still_connected(self) -> bool:
        # Try to connect to dummy client
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            try:
                client.connect(SOCKET_PATH)
                self.server.setblocking(False)
                client, _ = self.server.accept()
                self.server.setblocking(True)
                return True
            except BlockingIOError:
                return False # couldn't accept dummy client
            except OSError:
                return False # accept throws invalid argument if we never had a connection

    def __exit__(self, exc_type, exc_value, traceback):
        # Remove our old socket if we were using it
        if self.socket_available and self.still_connected():
            self.server.close()
            if os.path.exists(SOCKET_PATH):
                os.remove(SOCKET_PATH)

        # Exceptions we expect
        if exc_type == OSError:
            print("Socket already in use, use --override to usurp")
            return True # silence error
        elif exc_type in {EOFError, KeyboardInterrupt}:
            print("Interrupted, exiting")
            return True # silence error

        # Any other exception, don't silence
        elif exc_type: print("Exception:", exc_type.__name__)

        # No exception
        else: print("Quitting server")

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
                        reinit_thread = threading.Thread(target=self.get_device, args=())
                        reinit_thread.start()

            except ConnectionResetError:
                print("Client's recv not big enough for server request, failed")
                return
            except json.decoder.JSONDecodeError:
                # couldn't receive anything, we're done
                return
