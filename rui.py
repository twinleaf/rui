import sys, time
from rpclib.rpclib import SOCKET_PATH

from client.main import main as client_main
from client.itl import itl

from daemon.main import main as daemon_main
from daemon.server import send_eof

from test.record import record, list_recorded
from test.playback import run_transcript

if __name__ == "__main__":
    args = sys.argv[1:]

    try:
        match args:
            case ['daemon', *rest]:
                daemon_main(rest)

            case ['itl', *rest]:
                itl()

            case ['record', *rest]:
                daemon_main(["test", "--thread", "--silent"])
                try:
                    record(client_main, rest)
                finally:
                    send_eof(SOCKET_PATH)

            case ['playback', *rest]:
                passed, total = 0, 0
                for test in list_recorded():
                    daemon_main(["test", "--thread"])
                    total += 1
                    time.sleep(0.2)
                    try:
                        passed += run_transcript(client_main, test)
                    finally:
                        send_eof(SOCKET_PATH)
                print(f"RESULTS: PASSED {passed} OUT OF {total}")
            case _:
                client_main(args)
    except (EOFError, KeyboardInterrupt):
        print("\nInterrupted, exiting")
