import os, sys
from client.cli import main
from daemon.daemon import RPCDaemon

from test.testdev import TestDevice
from test.record import record, list_recorded
from test.playback import run_transcript

if __name__ == "__main__":
    args = sys.argv[1:]
    try:
        match args[0]:
            case 'daemon':
                if 'test' not in args:
                    import twinleaf
                    dev_constructor = twinleaf.Device
                else: dev_constructor = TestDevice

                with RPCDaemon(dev_constructor, '--override' in args) as daemon:
                    daemon.get_device()
                    daemon.server_loop()

            case 'record':
                # TODO: spawn daemon thread
                try:
                    record(main, args)
                except (EOFError, KeyboardInterrupt):
                    # shoudl never make our test
                    sys.exit("Interrupted, exiting")

            case 'playback':
                for test in list_recorded():
                    # TODO: daemon thread for each test
                    run_transcript(main, test)
            case _:
                main(args)
    except IndexError:
        main(args)
