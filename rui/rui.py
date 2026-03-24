import sys, argparse
from typing import Callable
from .cli import cli
from .gui import gui
from .device import Device

from .test.testdev import TestDevice
from .test.record import record
from .test.playback import playback
from .test.rerecord import rerecord

def _parser_setup(p: argparse.ArgumentParser, *, flags: str='',
                 func: Callable[[argparse.ArgumentParser], None]):
    """ Add TIO and optional RUI options to a subcommand parser """
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

def _parse_cli_args(args: argparse.Namespace):
    """ Iterate through non-flag options to find search terms and rpc arg for CLI """
    default_arg, search_terms = None, []
    for arg in args.cli_args:
        try: default_arg = float(arg)
        except ValueError: search_terms.append(arg)
    setattr(args, 'default_arg', default_arg)
    setattr(args, 'terms', search_terms)

def rui_parse_args() -> argparse.Namespace:
    """ Define parsers for RUI, parse sys.argv, and return created namespace """
    ### parser setup ###
    parser = argparse.ArgumentParser(
            description="RUI - Rpc User Interface for easy control of Twinleaf devices")

    subparsers = parser.add_subparsers(dest='command', help="Subcommands")

    ### main subparsers ###
    cli_parser = subparsers.add_parser('cli', help="[default] Command line RPC search/call")
    _parser_setup(cli_parser, flags='taemp*', func=cli)

    gui_parser = subparsers.add_parser('gui', help="RPC slider pop-out")
    _parser_setup(gui_parser, flags='taem*', func=gui)

    ### aux subparsers ###
    cache_parser = subparsers.add_parser('cache', help="RPC cache functions")
    cache_subparsers = cache_parser.add_subparsers(dest='cache_command', help="Actions")

    print_parser = cache_subparsers.add_parser('print', help="Print device RPC cache")
    _parser_setup(print_parser, flags='t', func=lambda d, _a: d.print_cache())

    remove_parser = cache_subparsers.add_parser('remove', help="Remove device RPC cache")
    _parser_setup(remove_parser, flags='t', func=lambda d, _a: d.remove_cache())

    ## hidden test subparsers ###
    record_func = lambda _d, _a: record(rui, sys.argv[2:], default_args=['--test'])
    playback_func = lambda _d, _a: playback(rui, default_args=['--test'])
    rerecord_func = lambda _d, _a: rerecord(rui, default_args=['--test'])

    record_parser = subparsers.add_parser('record', help="[dev] Record a test")
    _parser_setup(record_parser, flags='aemp*', func=record_func)

    playback_parser = subparsers.add_parser('playback', help="[dev] Playback tests")
    _parser_setup(playback_parser, func=playback_func)

    rerecord_parser = subparsers.add_parser('rerecord', help="[dev] Rerecord tests")
    _parser_setup(rerecord_parser, func=rerecord_func)

    # CLI is default arg
    subcommands = {'-h', '--help',
                   'cli', 'gui', 'cache',
                   'record', 'playback', 'rerecord'}
    if not sys.argv[1:] or not any([sys.argv[1] == arg for arg in subcommands]):
        sys.argv.insert(1, 'cli')
    if sys.argv[1:] and sys.argv[1] == 'cache':
        if not sys.argv[2:] or sys.argv[2] not in { 'print', 'remove', '-h', '--help', }:
            sys.argv.insert(2, '--help')

    args = parser.parse_args()
    if hasattr(args, 'cli_args'):
        _parse_cli_args(args)

    return args

def get_device(args):
    """ Get a Device or TestDevice based on RUI options """
    instantiate = args.command != 'cache' # don't instantiate cache in cache subcommand
    if hasattr(args, 'test') and not args.test:
        try:
            return Device(args.root, args.sensor, instantiate)
        except Device.InitError as e:
            print(str(e), file=sys.stderr)
            print("RUI: Couldn't initialize a device.\n" +
                 f"Might want to check root: {args.root} & sensor: {args.sensor}",
                  file=sys.stderr)
            sys.exit()
    else:
        return TestDevice()

def rui():
    """ RUI main script """
    args = rui_parse_args()
    dev = get_device(args)

    try:
        args.func(dev, args)
    except (EOFError, KeyboardInterrupt):
        print("\nInterrupted, exiting")
