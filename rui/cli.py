from typing import Callable
from rui.rpc import RPCList, RPCClient, rpc_type

def cli(dev, args):
    client = RPCClient(dev)
    try:
        selected = search_select(client.list, args.terms, args.exact, args.all)
        input_call_output(selected, args.default_arg, args.peek)
    except InputQuit: return

'''                         ''
    Select RPCs from list
''                         '''
def search_select(full_list: RPCList, search_terms: list[str],
                  exact: bool, select_all: bool#, match_any: bool
                  ) -> RPCList:
    terms = __valid_input(SEARCH_PROMPT, "", SEARCH_TEST, default=search_terms)
    if exact: terms = ['@' + term if term[0] != '@' else term for term in terms]

    matched = full_list.search(terms)
    matched.print()
    if matched.empty():
        print(MATCH_ERR(terms))
        return RPCList()
    else:
        if select_all:
            return matched
        else:
            selected = __select_input(matched)
            if not selected: print("Didn't select anything")
            return selected

def __select_input(matched: RPCList) -> RPCList:
    if matched.lonely(): return matched
    return __valid_input(SELECT_PROMPT,
                         SELECT_ERR(matched),
                         lambda x: __select_rpcs(matched, x))

def __select_rpcs(matched: RPCList, selection: str) -> RPCList:
    if selection[0] == '/':
        # Recursive case, go back to select_input with narrowed search
        return __select_input(matched.search(selection[1:].split()))
    elif selection == '*':
        return matched.pick([i for i in range(len(matched))])
    else:
        return matched.pick([int(s)-1 for s in selection.split()])

'''                         ''
    RPC command line calls
''                         '''
def input_call_output(selected: RPCList, cli_arg: rpc_type, peek: bool):
    for rpc in selected:
        # Print where we are in the call list
        if len(selected) > 1:
            print(rpc)

        # Let the user know the current/previous value
        if peek or rpc.arg_type == None:
            arg = None
        else:
            current = rpc.call()
            print(CURRENT_VAL_MSG(cli_arg, current))
            arg = __valid_input(ARG_PROMPT, ARG_ERR(rpc), ARG_TEST(rpc), default=cli_arg)

        # Make call and print new value
        output = rpc.call(arg)
        print("Reply:", output)

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

def __valid_input(input_msg: str, error_msg: str, test: Callable, default=None):
    # Get input/default, try to apply test and return
    try: return test(__input(input_msg, default))

    # If that didn't work, recurse until they get it right
    except (ValueError, IndexError):
        print(error_msg, end='')
        return __valid_input(input_msg, error_msg, test)

SEARCH_PROMPT = "Enter search terms: "
SEARCH_TEST = lambda t: t if t[0] is not None and type(t) is list else t.split()
MATCH_ERR = lambda t: f"Couldn't find {t[0] if len(t)==1 else 'a match'}."

SELECT_PROMPT = "Select rpc, or /[search] to keep searching: "
SELECT_ERR = lambda l: f"Invalid. Select a number from 1 to {len(l)}.\n"

ARG_PROMPT = "Enter argument: "
ARG_ERR = lambda r: f"Invalid. Argument should be of {str(r.arg_type)[1:-1]}.\n"
ARG_TEST = lambda r: lambda x: r.arg_type(x) if x not in {'-', ''} else None

CURRENT_VAL_MSG = lambda a, v: f"Previously: {v}" if a is not None else f"Currently: {v}"
