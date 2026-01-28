import os, sys
from client.cli import main
from daemon.daemon import RPCDaemon

from test.testdev import TestDevice
from test.record import record, list_recorded
from test.playback import run_transcript

if __name__ == "__main__":
    try:
        match sys.argv.pop(1):
            case 'daemon':
                if 'test' not in sys.argv:
                    import twinleaf
                    dev_constructor = twinleaf.Device
                else: dev_constructor = TestDevice

                with RPCDaemon(dev_constructor, '--override' in sys.argv) as daemon:
                    daemon.server_loop()
            case 'record':
                with RPCDaemon(dev_constructor, True) as daemon:
                    try:
                        record(main)
                    except (EOFError, KeyboardInterrupt):
                        print("Interrupted, exiting")
            case 'playback':
                for test in list_recorded():
                    # new daemon for every test
                    with RPCDaemon(dev_constructor, True) as daemon:
                        run_transcript(main, test)
            case _:
                main()
    except IndexError:
        main()
