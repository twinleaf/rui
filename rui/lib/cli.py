import sys
from typing import TypeVar, Callable
from rui.lib.rpc import RPC, RPCList

ALL_MODES = {'-', '++', '*', '@'}
FLAGS = {
        'no-arg': '-',
        'sliders': '++',
        'slider': '++',
        'select-all': '*',
        'exact': '@',
        }

class rpcCLI:
    '''Interface to parse and store command line input to RUI'''
    def __init__(self, argv: list[str]):
        self.search_terms = []  # list of search terms
        self.default_arg = None # argument to call rpc with, should be numeric
        self.modes = set()      # set of options from ALL_MODES
        self.__parse_args(argv)

    def __parse_args(self, argv: list[str]):
        for arg in argv:

            # If we have a mode option/flag, go to that
            if arg in ALL_MODES: self.add_mode(arg)
            elif arg[:2] == '--' and arg[2:] in FLAGS:
                self.add_mode(FLAGS[arg[2:]])

            else:
                # Otherwise, check if this arg is numeric.
                # If it is, assume it's meant to be an RPC argument
                try: self.default_arg = float(arg) if '.' in arg else int(arg)

                # If that fails, we can assume this is a search term
                except ValueError: self.search_terms.append(arg)

    def terms(self) -> list[str]:
        # lambda fails on "" or [], else splits by space if string or just returns list
        terms = valid_input("Enter search terms: ", "", # no error message
                            lambda t: t if t[0] is not None and type(t) is list else t.split(),
                            default=self.search_terms)

        # Add the exact flag to terms that aren't already exact
        # TODO: different way to exit search?
        # TODO: also indicate that - is no arg
        if self.exact(): terms = ['@' + term if term[0] != '@'
                                  else term for term in terms]

        # Save and return
        self.search_terms = terms
        return terms

    def add_mode(self, mode: str): self.modes.add(mode)
    def star(self) -> bool: return '*' in self.modes # select all rpcs
    def dash(self) -> bool: return '-' in self.modes # no argument
    def slider(self) -> bool: return '++' in self.modes # Qt slider
    def exact(self) -> bool: return '@' in self.modes # exact instead of fuzzy match

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
    # Get input/default, try to apply test and return
    try: return test(__input(input_msg, default))

    # If that didn't work, recurse until they get it right
    except (ValueError, IndexError):
        print(error_msg, end='')
        return valid_input(input_msg, error_msg, test)
