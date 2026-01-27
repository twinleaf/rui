#/home/zhao/.basevenv/bin/python
import sys
from daemon.daemon import RPCDaemon, TestDaemon

if __name__ == "__main__":
    try: 
        if len(sys.argv) > 1 and sys.argv[1] == 'test':
            daemon: RPCDaemon = TestDaemon()
        else:
            daemon = RPCDaemon()
        while True: daemon.server_loop()
    except (EOFError, KeyboardInterrupt):
        print("Interrupted, exiting")
