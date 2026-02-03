import os, pty, time, json, socket, select, threading
from rpclib.rpclib import SOCKET_PATH, PROXY_ERROR
from daemon.process import process_request
from daemon.server import DaemonServer

class RPCDaemon(DaemonServer):
    '''Handles starting daemon, twinleaf.Device, & receiving client requests'''
    def __init__(self, dev_constructor, socket_override=False, silent=False):
        super().__init__(SOCKET_PATH, socket_override, silent)
        self.dev_constructor    = dev_constructor
        self.dev                = None

    def setup(self):
        while True:
            try:
                if not self.silent: print("Looking for device...")
                self.dev = self.dev_constructor()
                if not self.silent:
                    print(f"Got device {self.dev.settings.dev.name().decode()}")
                break # go to return

            # dev_constructor will raise this if no device
            except RuntimeError:
                self.dev = None
                if not self.silent: print("Device not found, trying again in 5s...")
                time.sleep(5)

    def process_request(self, request: str):
        reply = process_request(self.dev, request)

        # If we got a proxy error and we aren't already, reinit device
        if reply == PROXY_ERROR and self.dev is not None:
            self.dev = None
            self.setup_thread()

        # process_request bounces itl back to us, we make it happen
        elif reply == "ITL":
            try: # try 5 socket files
                reply = [p for p in [f"/tmp/itl{i}.sock" for i in range(5)]
                         if not os.path.exists(p)][0]
            except IndexError:
                reply = ""

            itl_thread = threading.Thread(target=self.itl, args=(reply,), daemon=True)
            itl_thread.start()

        return reply

    def itl(self, socket_path: str):
        # Couldn't find a path
        if not socket_path: return

        with DaemonServer(socket_path) as itl_server:
            # Use DaemonServer framework but don't server_loop
            itl_server.make_server()
            pid, master_fd = pty.fork()

            if pid == 0: # we're child, become itl
                self.dev._interact()
                os._exit(0) # die when _interact ends, child doesn't clean up

            # otherwise, we're parent
            try:
                client, _ = itl_server.server.accept() # block here until client arrives
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
