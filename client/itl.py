import os, sys, time, socket, select, termios, tty
from rpclib.rpclib import SOCKET_PATH
from client.lib.send_request import send_request

# TODO: handle ProxyError
def itl():
    try:
        stdin_fd = sys.stdin.fileno()
        old_terminal = termios.tcgetattr(stdin_fd)
        tty.setraw(stdin_fd)

        path = send_request({'op': 'itl'})
        time.sleep(0.01) # wait for request)

        if not path:
            print("No path found!")
            return # no path found
        print(path)

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
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

    # un-raw our terminal
    finally: termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_terminal)
