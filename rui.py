import os, sys, time, signal
from rpclib.rpclib import SOCKET_PATH

from client.main import main as client_main
from client.itl import itl, kill_itl

from daemon.main import main as daemon_main
from daemon.server import send_eof

from test.record import record, list_recorded
from test.playback import run_transcript
from test.rerecord import rerecord_transcript

if __name__ == "__main__":
    # Handle SIGTERM and SIGINT as errors so we close sockets
    def sigterm_handler(signum, frame): raise SystemExit
    def sigint_handler(signum, frame): raise KeyboardInterrupt
    try:
        signal.signal(signal.SIGTERM, sigterm_handler)
        signal.signal(signal.SIGINT,  sigint_handler)
    except ValueError: pass # we're not a main thread

    args = sys.argv[1:]

    try:
        match args:
            case ['daemon', *rest]:
                daemon_main(rest)

            case ['itl', *rest]:
                itl()

            case ['killitl', path, *rest]:
                kill_itl(path)

            case ['record', *rest]:
                daemon_main(["test", "--thread"])

                try:
                    record(client_main, rest)
                finally:
                    send_eof(SOCKET_PATH)

            case ['playback', *rest]:
                passed, total = 0, 0
                for test in list_recorded():
                    daemon_main(["test", "--thread"])
                    total += 1
                    while not os.path.exists(SOCKET_PATH): pass

                    try:
                        passed += run_transcript(client_main, test)
                    finally:
                        send_eof(SOCKET_PATH)
                        print() # spacer
                print(f"RESULTS: PASSED {passed} OUT OF {total}")

            case ['rerecord', *rest]:
                for test in list_recorded():
                    daemon_main(["test", "--thread"])
                    while not os.path.exists(SOCKET_PATH): pass

                    try:
                        passed = run_transcript(client_main, test, silent=True)
                    finally:
                        send_eof(SOCKET_PATH)

                    if passed:
                        print(test.name, "passed")
                    else:
                        daemon_main(["test", "--thread"])
                        while not os.path.exists(SOCKET_PATH): pass
                        try:
                            rerecord_transcript(client_main, test)
                        finally:
                            send_eof(SOCKET_PATH)
                            print() # spacer

            case _:
                client_main(args)
    except (EOFError, KeyboardInterrupt):
        print("\nInterrupted, exiting")
