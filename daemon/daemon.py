import os, time, json, socket, threading
from rpclib.tio import SOCKET_PATH, PROXY_ERROR
from .process import process_request

class RPCDaemon:
    '''Handles starting daemon, twinleaf.Device, & receiving client requests'''
    def __init__(self, dev_constructor, server_override=False, silent=False):
        self.dev_constructor    = dev_constructor
        self.path               = SOCKET_PATH
        self.server_override    = server_override
        self.silent             = silent
        self.socket_available   = False
        self.dev                = None
        self.server             = None

    def __enter__(self):
        ''' Called as we enter a with statement, gets device only if socket available '''
        self.socket_available = not os.path.exists(self.path)

        # If override, we can't kill the old server but we can usurp its socket
        if self.server_override and not self.socket_available:
            os.remove(self.path)
            self.socket_available = True

        # If we have a socket, set up server and make device
        if self.socket_available: self._make_server()
        while self.socket_available:
            try:
                if not self.silent: print("Looking for device...")
                self.dev = self.dev_constructor()
                if not self.silent: print(f"Got device {self.dev.settings.dev.name().decode()}")
                break # go to return

            # dev_constructor will raise this if no device
            except RuntimeError:
                self.dev = None
                if not self.silent: print("Device not found, trying again in 5s...")
                time.sleep(5)

        return self

    def server_loop(self):
        ''' Call inside with statement to actually run server '''
        if not self.socket_available: raise OSError # We don't have a server, exit
        while True:
            assert self._still_connected()
            client, _ = self.server.accept() # block here until client arrives
            client_thread = threading.Thread(target=self._handle_client,
                                    args=(client,), daemon=True)
            client_thread.start()

    def __exit__(self, exc_type, exc_value, traceback):
        ''' Called as we gracefully exit a with statement '''

        # Remove our old socket if we were using it
        if self.socket_available and self._still_connected():
            self.server.close()
            if os.path.exists(self.path):
                os.remove(self.path)

        # Exceptions we expect
        if exc_type == OSError:
            print("Socket already in use, use --override to usurp")
            return True # silence error
        elif exc_type == AssertionError:
            print("Lost connection, exiting")
            return True
        elif exc_type == SystemExit:
            return True

        # Any other exception, don't silence
        elif exc_type: return False

        # No exception, no return needed
        else:
            if not self.silent: print("Quitting server")

    def _make_server(self):
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.bind(self.path) # raise OSError if socket in use
        self.server.listen(5) # accept up to five clients (arbitrary)
        if not self.silent: print("Started server")

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
            except BrokenPipeError:
                # client died before we could send, whatever
                return
            except json.decoder.JSONDecodeError:
                # couldn't receive anything, we're done
                return

    def _still_connected(self) -> bool:
        # Try to connect to dummy client
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            try:
                client.connect(self.path)
                client, _ = self.server.accept()
                return True
            except BlockingIOError:
                return False # couldn't accept dummy client
            except OSError:
                return False # accept throws invalid argument if we never had a connection
            # TODO: does ConnectionResetError happen here and what causes it?
