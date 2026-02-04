import os, sys, socket, select, termios, tty
from rpclib.rpclib import SOCKET_PATH
from client.lib.send_request import send_request

# TODO: handle ProxyError
def itl():
    path = send_request({'op': 'itl'})
    if not path: raise SystemExit("No path found!")
    else: print(path)

    # Wait for path to exist
    while not os.path.exists(path): 
        print('a', end='')

    stdin_fd = sys.stdin.fileno()
    old_terminal = termios.tcgetattr(stdin_fd)
    tty.setraw(stdin_fd)

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        try:
            client.connect(path)

            while True:
                r, _, _ = select.select([client, sys.stdin], [], [])

                if client in r:
                    data = client.recv(8192)
                    if not data: break
                    sys.stdout.buffer.write(data)
                    sys.stdout.flush()

                if sys.stdin in r:
                    data = os.read(stdin_fd, 8192)
                    client.sendall(data)
        finally: 
            # un-raw our terminal
            termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_terminal)
            try: client.sendall("__ITL_EOF".encode())
            except: pass # this can go wrong in all sorts of ways

def kill_itl(kill_path: str):
    if os.path.exists(kill_path):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(kill_path)
            try: client.sendall("__ITL_EOF".encode())
            except: pass
