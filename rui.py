#!/usr/bin/env -S bash -c 'exec "$HOME/python/bin/python" "$0" "$@"'
import sys, argparse
from typing import Callable
from rui.cli import cli
from rui.gui import gui
from rui.device import Device

from test.testdev import TestDevice
from test.record import record
from test.playback import playback
from test.rerecord import rerecord

def parser_setup(p: argparse.ArgumentParser, *, flags: str='',
                 func: Callable[[argparse.ArgumentParser], None]):
    p.set_defaults(func=func)
    if flags:
        # global flags
        p.add_argument('-r', '--root', action='store', default="tcp://localhost",
                       help="Sensor root address")
        p.add_argument('-s', '--sensor', default='/',
                       help="Sensor path in the sensor tree")

        # optional flags
        if 't' in flags:
            p.add_argument('--test', action='store_true', help=argparse.SUPPRESS)
        if 'a' in flags:
            p.add_argument('-a', '--all', action='store_true',
                           help="Select all matched RPCs")
        if 'e' in flags:
            p.add_argument('-e', '--exact', action='store_true',
                           help="Search exactly instead of fuzzily")
        if 'm' in flags:
            p.add_argument('-m', '--multisearch',  action='store_true',
                           help="Search multiple terms at once")
        if 'p' in flags:
            p.add_argument('-p', '--peek', action='store_true',
                           help="Don't prompt to change RPC value")
        if '*' in flags:
            p.add_argument('cli_args', nargs='*', metavar="search terms [+arg]",
                           help="RPC search terms and argument to call with")

def parse_cli_args(args: argparse.Namespace):
    default_arg, search_terms = None, []
    for arg in args.cli_args:
        try: default_arg = float(arg)
        except ValueError: search_terms.append(arg)
    setattr(args, 'default_arg', default_arg)
    setattr(args, 'terms', search_terms)

def record_main(*args): record(main, sys.argv[2:], default_args=['--test'])
def playback_main(*args): playback(main, default_args=['--test'])
def rerecord_main(*args): rerecord(main, default_args=['--test'])

def rui_parse_args() -> argparse.Namespace:
    ### parser setup ###
    parser = argparse.ArgumentParser(
            description="RUI - Rpc User Interface for easy control of Twinleaf devices")
    subparsers = parser.add_subparsers(dest='command', help="Available subcommands")

    ### main subparsers ###
    cli_parser = subparsers.add_parser('cli', help="Command line RPC search/call")
    parser_setup(cli_parser, flags='taemp*', func=cli)

    gui_parser = subparsers.add_parser('gui', help="RPC slider pop-out")
    parser_setup(gui_parser, flags='taem*', func=gui)

    itl_parser = subparsers.add_parser('itl', help="Twinleaf IPython with RPC cache")
    parser_setup(itl_parser, flags='t', func=lambda d, _a: d._interact())

    ## hidden test subparsers ###
    record_parser = subparsers.add_parser('record', help="[dev] Record a test")
    parser_setup(record_parser, flags='aemp*', func=record_main)

    playback_parser = subparsers.add_parser('playback', help="[dev] Playback tests")
    parser_setup(playback_parser, func=playback_main)

    rerecord_parser = subparsers.add_parser('rerecord', help="[dev] Rerecord tests")
    parser_setup(rerecord_parser, func=rerecord_main)

    # CLI is default arg
    subcommands = ['-h', '--help',
                   'cli', 'gui', 'itl',
                   'record', 'playback', 'rerecord']
    if not any([arg in sys.argv for arg in subcommands]):
        sys.argv.insert(1, 'cli')

    args = parser.parse_args()
    if hasattr(args, 'cli_args'):
        parse_cli_args(args)

    return args

def get_device(args):
    if hasattr(args, 'test') and not args.test:
        try:
            return Device(args.root, args.sensor)
        except Device.InitError as e:
            print(str(e), file=sys.stderr)
            print("RUI: Couldn't initialize a device.\n" +
                 f"Might want to check root: {args.root} & sensor: {args.sensor}",
                  file=sys.stderr)
            sys.exit()
    else:
        return TestDevice()

def main():
    args = rui_parse_args()
    dev = get_device(args)
    args.func(dev, args)

if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nInterrupted, exiting")
