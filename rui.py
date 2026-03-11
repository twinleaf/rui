#!/usr/bin/env -S bash -c 'exec "$HOME/python/bin/python" "$0" "$@"'
import sys, argparse
from rui.cli import cli
from rui.gui import gui
from rui.device import Device

from test.testdev import TestDevice
from test.record import record
from test.playback import playback
from test.rerecord import rerecord

def add_global_opts(p: argparse.ArgumentParser):
    p.add_argument('-r', '--root', action='store', default="tcp://localhost",
                   help="Sensor root address")
    p.add_argument('-s', '--sensor', default='/',
                   help="Sensor path in the sensor tree")

def add_search_opts(p: argparse.ArgumentParser):
    p.add_argument('-a', '--all', action='store_true',
                   help="Select all matched RPCs")
    p.add_argument('-e', '--exact', action='store_true',
                   help="Search exactly instead of fuzzily")
    p.add_argument('-m', '--multisearch',  action='store_true',
                   help="Search multiple terms at once")
    p.add_argument('rui_args', nargs='*', metavar="search terms [+arg]",
                   help="RPC search terms and argument to call with")

def parse_rui_args(rui_args: list[str]) -> tuple[float, list[str]]:
    default_arg, search_terms = None, []
    for arg in rui_args:
        try: default_arg = float(arg)
        except ValueError: search_terms.append(arg)
    return default_arg, search_terms

def main():
    ### parser setup ###
    parser = argparse.ArgumentParser(
            description="RUI - Rpc User Interface for easy control of Twinleaf devices")
    subparsers = parser.add_subparsers(dest='command', help="Available subcommands")

    ### main subparsers ###
    cli_parser = subparsers.add_parser('cli', help="Command line RPC search/call")
    cli_parser.set_defaults(func=cli)
    cli_parser.add_argument('-p', '--peek', action='store_true',
                            help="Don't prompt to change RPC value")
    cli_parser.add_argument('--test', action='store_true', help=argparse.SUPPRESS)
    add_global_opts(cli_parser)
    add_search_opts(cli_parser)

    gui_parser = subparsers.add_parser('gui', help="RPC slider pop-out")
    gui_parser.set_defaults(func=gui)
    gui_parser.add_argument('--test', action='store_true', help=argparse.SUPPRESS)
    add_global_opts(gui_parser)
    add_search_opts(gui_parser)

    itl_parser = subparsers.add_parser('itl', help="Twinleaf IPython with RPC cache")
    itl_parser.set_defaults(func=lambda d, _a: d._interact())
    add_global_opts(itl_parser)

    ## hidden test subparsers ###
    record_parser = subparsers.add_parser('record', help=argparse.SUPPRESS)
    record_parser.set_defaults(func=lambda _d, _a: record(main, sys.argv[2:],
                                                          default_args=["--test"]))
    add_global_opts(record_parser)
    add_search_opts(record_parser)
    playback_parser = subparsers.add_parser('playback', help=argparse.SUPPRESS)
    playback_parser.set_defaults(func=lambda _d, _a: playback(main, default_args=["--test"]))
    rerecord_parser = subparsers.add_parser('rerecord', help=argparse.SUPPRESS)
    rerecord_parser.set_defaults(func=lambda _d, _a: rerecord(main, default_args=["--test"]))

    # CLI is default arg
    subcommands = ['-h', '--hlp',
                   'cli', 'gui', 'itl',
                   'record', 'playback', 'rerecord']
    if not any([arg in sys.argv for arg in subcommands]):
        sys.argv.insert(1, 'cli')

    args = parser.parse_args()
    try:
        if hasattr(args, 'test') and not args.test:
            try:
                dev = Device(args.root, args.sensor)
            except BaseException as e:
                if type(e) is SystemExit:
                    print(e)
                print("\nRUI: Couldn't initialize a device.")
                print(f"Might want to check root: {args.root} & sensor: {args.sensor}")
                return

        else:
            dev = TestDevice()
        if hasattr(args, 'rui_args'):
            default_arg, search_terms = parse_rui_args(args.rui_args)
            setattr(args, 'default_arg', default_arg)
            setattr(args, 'terms', search_terms)

        args.func(dev, args)
    except (EOFError, KeyboardInterrupt):
        print("\nInterrupted, exiting")

if __name__ == "__main__":
   main()
