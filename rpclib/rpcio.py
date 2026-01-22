import sys
from typing import TypeVar, Callable
from .rpc import RPC, RPCList

'''           ''
    I/O core
''           '''

SEARCH_PROMPT = "Enter search terms: "
SEARCH_ERR = ""
SEARCH_TEST = lambda x: __terms_to_list(x)
def __terms_to_list(terms: str | list[str]) -> list[str]:
    if type(terms) is str: terms = terms.split()
    if terms == []: raise ValueError("no terms")
    return list(terms)

SELECT_PROMPT = "Select rpc, or /[search] to keep searching: "
SELECT_ERR = lambda l: f"Invalid. Select a number from 1 to {len(l)}.\n"
SELECT_TEST = lambda l, m: lambda x: __select_rpcs(l, x, m) if x != '\\' else RPCList()
def __select_rpcs(rpcs: RPCList, selection: str, match_any: bool=False) -> RPCList:
    if selection[0] == '/':
        # narrow search by recursively calling select_input
        return select_input(rpcs.search(selection.split(), match_any))
    elif selection == '*':
        return rpcs.pick([i for i in range(len(rpcs))]) # pick all
    elif len(selection.split()) == 1:
        return rpcs.pick([int(selection)-1])
    else:
        return rpcs.pick([int(s)-1 for s in selection.split()])

ARG_PROMPT = "Enter argument: "
ARG_ERR = lambda r: f"Invalid. Argument should be of {str(r.arg_type)[1:-1]}.\n"
ARG_TEST = lambda r: lambda x: r.arg_type(x) if x not in {'-', ''} else None

def __input(msg: str, default=None):
    if default is not None: return default
    try:
        i = input(msg)
        if i == "quit" or i == "exit": sys.exit(0)
        return i
    except (EOFError, KeyboardInterrupt):
        print("\nInterrupted, exiting")
        sys.exit(2)

RT = TypeVar('RT')
def valid_input(input_msg: str, error_msg: str,
                test: Callable[[str], RT], default=None) -> RT:
    try: return test(__input(input_msg, default))
    except (ValueError, IndexError):
        print(error_msg, end='')
        return valid_input(input_msg, error_msg, test) # recurse until they get it right

def search_input(search_terms: list[str]) -> list[str]:
    return valid_input(SEARCH_PROMPT, SEARCH_ERR, SEARCH_TEST, default=search_terms)

def select_input(rpclist: RPCList, star: bool=False, slash: bool=False) -> RPCList:
    rpclist.print()
    if rpclist.lonely() or star: return rpclist
    else: return valid_input(SELECT_PROMPT, SELECT_ERR(rpclist), SELECT_TEST(rpclist, slash))

def arg_input(rpc: RPC, default=None): # -> rpc.arg_type
    return valid_input(ARG_PROMPT, ARG_ERR(rpc), ARG_TEST(rpc), default=default)
