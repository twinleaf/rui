#!/usr/bin/env -S bash -c 'exec "$HOME/python/bin/python" "$0" "$@"'
import os, sys, time
import twinleaf

from rui.main import main
from rui.lib.rpc import get_dev_list
from rui.gui import slider
from rui.device import Device

from test.testdev import TestDevice
from test.record import record
from test.playback import playback
from test.rerecord import rerecord_transcripts

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
                playback(test_main())
            case ['rerecord', *rest]:
                rerecord_transcripts(test_main())
            case ['slider' | 'sliders', *rest]:
                slider(get_dev_list(Device()))
            case []:
                main(Device(), [])
            case _:
                main(Device(), args)

    except (EOFError, KeyboardInterrupt):
        print("\nInterrupted, exiting")
