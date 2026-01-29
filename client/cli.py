import sys
from typing import TypeVar, Callable
from rpclib.rpc import RPC, RPCList
from rpclib.rpctypes import rpc_arg_type

ALL_MODES = {'-', '+', '++', '*', '@', '/', '|', 'debug', 'regen'}
FLAGS = {
        'no-arg': '-',
        'continuous': '+',
        'sliders': '++',
        'slider': '++',
        'select-all': '*',
        'exact': '@',
        'keep-searching': '/',
        'match-any': '|',
        'debug': 'debug',
        'regen': 'regen'
        }

class rpcCLI:
    '''Interface to parse and store command line input to findrpc'''
    def __init__(self, argv: list[str]):
        self.search_terms:  list[str] = []      # list of search terms
        self.default_arg:   rpc_arg_type = None # argument to call rpc with, should be numeric
        self.modes:         set[str]  = set()   # set of options from ALL_MODES
        self.__parse_args(argv)

    def __parse_args(self, argv: list[str]):
        for arg in argv:
            if arg in ALL_MODES:
                self.add_mode(arg)
            elif arg[:2] == '--' and arg[2:] in FLAGS:
                self.add_mode(FLAGS[arg[2:]])
            else:
                try: self.default_arg = float(arg) if '.' in arg else int(arg)
                except ValueError: self.search_terms.append(arg)

    def terms(self) -> list[str]:
        terms = valid_input("Enter search terms: ", "", # no error message
                            lambda t: t if t[0] is not None and type(t) is list else t.split(),
                            default=self.search_terms)
        if self.exact(): terms = ['@' + term if term[0] not in {'\\', '@'}
                                  else term for term in terms]
        self.search_terms = terms
        return terms

    def add_mode(self, mode: str): self.modes.add(mode)
    def any(self) -> bool: return '|' in self.modes # match any term, not just all
    def star(self) -> bool: return '*' in self.modes # select all rpcs
    def dash(self) -> bool: return '-' in self.modes # no argument
    def plus(self) -> bool: return '+' in self.modes # loop calls forever
    def slash(self) -> bool: return '/' in self.modes # keep searching until \
    def slider(self) -> bool: return '++' in self.modes #Qt slider
    def exact(self) -> bool: return '@' in self.modes # exact instead of fuzzy match
    def regen(self) -> bool: return 'regen' in self.modes # regenerate rpc-list file
    def debug(self) -> bool: return 'debug' in self.modes # debug options

'''           ''
    I/O core
''           '''

class InputQuit(Exception): pass
def __input(msg: str, default=None):
    if default is not None: return default
    i = input(msg)
    if i == "quit" or i == "exit":
        raise InputQuit
    return i

RT = TypeVar('RT')
def valid_input(input_msg: str, error_msg: str,
                test: Callable[[str], RT], default=None) -> RT:
    try: return test(__input(input_msg, default))
    except (ValueError, IndexError):
        print(error_msg, end='')
        return valid_input(input_msg, error_msg, test) # recurse until they get it right
