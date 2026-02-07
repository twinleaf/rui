#!/usr/bin/env -S bash -c 'exec "$( dirname $0 )/../twinleaf-python/.rpcvenv/bin/python" "$0" "$@"'
import os, sys, time
import twinleaf

from rui.main import main

from test.testdev import TestDevice
from test.record import record, list_recorded
from test.playback import run_transcript
from test.rerecord import rerecord_transcript

if __name__ == "__main__":
    args = sys.argv[1:]

    try:
        match args:
            case ['itl', *rest]:
                twinleaf.Device()._interact()
            case ['test', *rest]:
                test_main = lambda args: main(TestDevice(), args)
                test_main(rest)
            case ['record', *rest]:
                test_main = lambda args: main(TestDevice(), args)
                record(test_main, rest)

            case ['playback', *rest]:
                passed = 0
                for test in list_recorded():
                    test_main = lambda args: main(TestDevice(), args)
                    passed += run_transcript(test_main, test)

                    print() # spacer
                print(f"RESULTS: PASSED {passed} OUT OF {len(list_recorded())}")

            case ['rerecord', *rest]:
                for test in list_recorded():
                    test_main = lambda args: main(TestDevice(), args)
                    passed = run_transcript(test_main, test, silent=True)

                    if not passed:
                        test_main = lambda args: main(TestDevice(), args)
                        rerecord_transcript(test_main, test)

                    print(test.name + " passed" if passed else "")

            case _:
                dev = twinleaf.Device(instantiate=False)
                dev._instantiate_rpcs()
                main(dev, args)

    except (EOFError, KeyboardInterrupt):
        print("\nInterrupted, exiting")
