import os, pty, time, json, socket, select, threading
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
        self.eof                = False
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
        if self.socket_available: 
            self.server = self._make_server(self.path)

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

    # TODO: this function can check if path exists / is available
    def _make_server(self, path: str) -> socket.socket:
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(path) # raise OSError if socket in use
        server.listen(5) # accept up to five clients (arbitrary)
        if not self.silent: print("Started server")
        return server

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

    def _handle_client(self, client: socket.socket):
        with client:
            try:
                while True:
                    # receive, process, and reply
                    request = json.loads(client.recv(8192).decode())
                    reply = process_request(self.dev, request)
                    
                    # if we're itl, we loop here forever
                    if reply == "ITL":
                        try: # try 5 socket files
                            path = [p for p in [f"/tmp/itl{i}.sock" for i in range(5)]
                                    if not os.path.exists(p)][0]
                        except IndexError:
                            path = ""
                        client.sendall( json.dumps({"rep": path}).encode() )
                        return self._itl(path)

                    # Send data to client
                    client.sendall( json.dumps({"rep": reply}).encode() )

                    # TODO: let client send EOF to kill server
                    if reply == "EOF": self.eof = True

                    # if we have a bad device, re-initalize it
                    elif reply == PROXY_ERROR and self.dev is not None:
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

    def _itl(self, socket_path: str):
        # Couldn't find a path
        if not socket_path: return

        try:
            itl_server = self._make_server(socket_path)
            pid, master_fd = pty.fork()

            if pid == 0: # we're child, become zsh
                os.execvp("zsh", ["zsh"])
                os._exit(0) # die when _interact ends, child doesn't clean up

            # otherwise, we're parent
            try:
                client, _ = itl_server.accept() # block here until client arrives
                with client:
                    while True:
                        # readable, writeable, error
                        r, _, _ = select.select([master_fd, client], [], [])

                        if master_fd in r: # child's stdout, send to client
                            data = os.read(master_fd, 8192)
                            if not data: break # child died
                            client.sendall(data)

                        if client in r: # client's stdin, send to child
                            data = client.recv(8192)
                            os.write(master_fd, data)
            except KeyboardInterrupt:
                print("Interrupted, exiting")
            except OSError:
                print("Client quit, exiting")
        finally:
            itl_server.close()
            if os.path.exists(socket_path):
                os.remove(socket_path)
