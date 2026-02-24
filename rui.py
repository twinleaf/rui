#!/usr/bin/env -S bash -c 'exec "$HOME/python/bin/python" "$0" "$@"'
import os, sys, time
import twinleaf

from rui.rpc import RPCClient
from rui.device import Device
from rui.main import main, HELP_MSG
from rui.gui import control_panel

from test.testdev import TestDevice
from test.record import record
from test.playback import playback
from test.rerecord import rerecord_transcripts

def test_main(): return lambda args: main(TestDevice(), args)

if __name__ == "__main__":
    args = sys.argv[1:]
    if 'test' in args:
        args.remove('test')
        Device = TestDevice
        main = test_main

    if '--url' in args:
        ind = args.index('--url')
        args.pop(ind)
        try:
            url = args.pop(ind)
        except IndexError:
            sys.exit("Need to specify a url after --url")
    else: url = None

    if '-s' in args:
        ind = args.index('-s')
        args.pop(ind)
        try:
            route = args.pop(ind)
        except IndexError:
            sys.exit("Need to specify a route after -s")
    else: route = None

    dev = lambda: Device() if type(Device) is TestDevice else Device(url, route)

    try:
        match args:
            case args if any(h in args for h in ['help', '-h', '--help']):
                print(HELP_MSG)
            case ['itl', *rest]:
                dev()._interact()
            case ['record', *rest]:
                record(test_main(), rest)
            case ['playback', *rest]:
                playback(test_main())
            case ['rerecord', *rest]:
                rerecord_transcripts(test_main())
            case ['gui']:
                control_panel(RPCClient(dev()).list)
            case ['gui', *rest]:
                main(dev(), ['+'] + rest)

            case args if 'regen' in args:
                args.remove('regen')
                dev = dev()
                with open(dev._cache_path(), 'w') as f:
                    dev._write_rpc_cache(f)
                main(dev(), args)
            case []:
                main(dev(), [])
            case _:
                main(dev(), args)

    except (EOFError, KeyboardInterrupt):
        print("\nInterrupted, exiting")
