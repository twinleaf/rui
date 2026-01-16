import sys
from typing import Any, Callable, TypeVar
from rpc import RPC
from rpclist import RPCList

'''           ''
    I/O core
''           '''

SEARCH_PROMPT = "Enter search terms: "
SEARCH_ERR = ""
SEARCH_TEST = lambda x:_terms_to_list(x)
def _terms_to_list(terms: str | list[str]) -> list[str]:
    if type(terms) is str: terms = terms.split()
    if terms==[]: raise ValueError("no terms")
    return list(terms)

SELECT_PROMPT = "Select rpc, or /[search] to keep searching: "
SELECT_ERR = lambda rpclist: f"Invalid. Select a number from 1 to {len(rpclist)}.\n"
SELECT_TEST = lambda rpclist: lambda x: rpclist.select(x)

ARG_PROMPT = lambda x: f"Enter {x}: "
ARG_ERR = lambda rpc: f"Invalid. Argument should be of {str(rpc.data_type)[1:-1]}.\n"
ARG_TEST = lambda rpc: lambda x: str(rpc.data_type(x)) if x!='-' else None

def _input(msg: str, default: Any=None) -> Any:
    if default is not None: return default
    try:
        i = input(msg)
        if i == '' or i == "quit" or i == "exit": sys.exit(0)
        return i
    except (EOFError, KeyboardInterrupt):
        print("\nInterrupted, exiting")
        sys.exit(2)

RT = TypeVar('RT')
def valid_input(input_msg: str, error_msg: str,
                test: Callable[[str], RT], default: Any=None) -> RT:
    try: return test(_input(input_msg, default))
    except (ValueError, IndexError):
        print(error_msg, end='')
        return valid_input(input_msg, error_msg, test) # recurse until they get it right

def select_input(rpclist: RPCList) -> RPCList:
    return valid_input(SELECT_PROMPT, SELECT_ERR(rpclist), SELECT_TEST(rpclist))

def search_input(search_terms: list[str]) -> list[str]:
    return valid_input(SEARCH_PROMPT, SEARCH_ERR, SEARCH_TEST, default=search_terms)

def arg_input(rpc: RPC, default: Any=None, prompt: str="argument"): # -> rpc.data_type
    return valid_input(ARG_PROMPT(prompt), ARG_ERR(rpc), ARG_TEST(rpc), default=default)
