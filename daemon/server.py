import os, time, json, socket, threading

class SocketOccupiedError(Exception): pass
class UnconnectedError(Exception): pass

def wait_for(socket_path: str):
    while not os.path.exists(socket_path): pass

def send_eof(socket_path: str):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        try: client.connect(socket_path)
        except FileNotFoundError: return # socket already died

        client.sendall(json.dumps({"op": "EOF"}).encode())
        client.recv(8192) # accept reply so server will get to EOF

class DaemonServer:
    ''' Generic class to represent daemon server using with statements'''
    def __init__(self, socket_path: str, socket_override=False, silent=False):
        self.socket_path = socket_path
        self.socket_override = socket_override
        self.silent = silent
        self.socket_available = False
        self.eof_received = False
        self.server = None

    def __enter__(self):
        # Check if we have a socket
        self.socket_available = not os.path.exists(self.socket_path)

        # Usurp the socket if we want to override
        if self.socket_override and not self.socket_available:
            # TODO: add error handling, for example ConnectionResetError
            send_eof(self.socket_path)
            self.socket_available = True

        return self

    # Replace in subclasses with whatever we need to set up the server
    def setup(self): pass

    # Setup in a thread so we don't block server loop
    def setup_thread(self):
        setup_thread = threading.Thread(target=self.setup, args=(), daemon=True)
        setup_thread.start()

    def make_server(self) -> socket.socket:
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        # Our path should be unoccupied, wait for the other server to give it up
        while os.path.exists(self.socket_path): pass
        self.server.bind(self.socket_path)

        self.server.listen(5) # accept 5 clients, arbitrary
        if not self.silent: print("Started server at " + self.socket_path)

    # Replace in subclasses with whatever we want to do with client's request
    def process_request(self, request): pass

    def handle_client(self, client: socket.socket):
        with client:
            try:
                while True:
                    request = json.loads(client.recv(8192).decode())
                    reply = self.process_request(request)
                    if request['op'] == "EOF": self.eof()
                    client.sendall(json.dumps({"rep": reply}).encode())
            except ConnectionResetError:
                print("Client's recv not big enough for server request, failed")
                return
            except BrokenPipeError:
                print("Client died before server could reply")
                return
            except json.decoder.JSONDecodeError: # Client disconnected
                return

    def server_loop(self):
        # If we don't have a socket at this point, error and go to __exit__
        if not self.socket_available: raise SocketOccupiedError

        self.make_server()
        self.setup_thread()

        while True:
            if self.eof_received: raise EOFError
            client, _ = self.server.accept() # block here until client arrives
            client_thread = threading.Thread(target = self.handle_client,
                                             args=(client,), daemon=True)
            client_thread.start()

    def eof(self):
        # Tell server to EOF, then make a dummy client so it doesn't get to blocking first
        self.eof_received = True
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(self.socket_path)

    def __exit__(self, exc_type, exc_value, traceback):
        if self.socket_available:

            # If we haven't been overridden, we can also remove the path
            if os.path.exists(self.socket_path):
                print("Removing socket " + self.socket_path)
                os.remove(self.socket_path)

            # Now we can close our server
            if self.server: self.server.close()

        # Exceptions we expect
        if exc_type == SocketOccupiedError:
            print("Socket already in use, use --override to usurp")
            return True # silence error
        elif exc_type == UnconnectedError:
            print("Lost connection, exiting")
            return True
        elif exc_type == EOFError:
            print("Sent EOF, exiting")
        elif exc_type == SystemExit:
            print("Termianted, exiting")
            return True

        # Any other exception, don't silence
        elif exc_type: return False

        # No exception, no return needed
        elif not self.silent: print("Quitting server")
