import os, sys, time
from client.main import main
from daemon.daemon import RPCDaemon
from daemon.spawn import spawn_test_daemon

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
                override = '--override' in rest

                with RPCDaemon(dev_constructor, override) as daemon:
                    daemon.server_loop()

            case ['record', *rest]:
                stop_signal = spawn_test_daemon(TestDevice)
                try:
                    record(main, rest)
                finally:
                    stop_signal.set()

            case ['playback', *rest]:
                passed, total = 0, 0
                for test in list_recorded():
                    stop_signal = spawn_test_daemon(TestDevice)
                    total += 1
                    try:
                        passed += run_transcript(main, test)
                    finally:
                        stop_signal.set()
                    time.sleep(0.4) # wait at least 0.3s for daemon to exit
                print(f"RESULTS: PASSED {passed} OUT OF {total}")
            case _:
                main(args)
    except (EOFError, KeyboardInterrupt):
        print("\nInterrupted, exiting")
