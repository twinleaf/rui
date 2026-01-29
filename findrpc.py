import os, sys
from client.main import main
from daemon.daemon import RPCDaemon
from daemon.spawn import spawn_temp_daemon

from test.testdev import TestDevice
from test.record import record, list_recorded
from test.playback import run_transcript

if __name__ == "__main__":
    args = sys.argv[1:]
    try:
        match args:
            case ['daemon', *rest]:
                if 'test' not in rest:
                    import twinleaf
                    dev_constructor = twinleaf.Device
                else: dev_constructor = TestDevice

                with RPCDaemon(dev_constructor, '--override' in rest) as daemon:
                    daemon.get_device()
                    daemon.server_loop()

            case ['record', *rest]:
                spawn_temp_daemon(TestDevice, True, True) # override, silent
                record(main, rest)

            case ['playback', *rest]:
                for test in list_recorded():
                    spawn_temp_daemon(TestDevice, True, True) # override, silent
                    run_transcript(main, test)
            case _:
                main(args)
    except (EOFError, KeyboardInterrupt):
        print("\nInterrupted, exiting")
