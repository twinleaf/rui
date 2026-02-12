#!/usr/bin/env -S bash -c 'exec "$HOME/python/bin/python" "$0" "$@"'
import os, sys, time
print(sys.executable)
import twinleaf

from rui.main import main
from rui.device import Device

from test.testdev import TestDevice
from test.record import record, list_recorded
from test.playback import run_transcript
from test.rerecord import rerecord_transcript

def test_main(): return lambda args: main(TestDevice(), args)

if __name__ == "__main__":
    args = sys.argv[1:]

    try:
        match args:
            case ['itl', *rest]:
                Device()._interact()
            case ['test', *rest]:
                test_main()(rest)
            case ['record', *rest]:
                record(test_main(), rest)

            case ['playback', *rest]:
                passed = 0
                for test in list_recorded():
                    passed += run_transcript(test_main(), test)

                    print() # spacer
                print(f"RESULTS: PASSED {passed} OUT OF {len(list_recorded())}")

            case ['rerecord', *rest]:
                for test in list_recorded():
                    passed = run_transcript(test_main(), test, silent=True)

                    if not passed:
                        rerecord_transcript(test_main(), test)

                    print(test.name + " passed" if passed else "")

            case _:
                main(Device(), args)

    except (EOFError, KeyboardInterrupt):
        print("\nInterrupted, exiting")
