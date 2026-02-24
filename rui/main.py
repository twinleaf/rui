import os, sys
from typing import TypeVar, Callable
from rui.rpc import RPC, RPCList, RPCClient, rpc_type
from rui.gui import control_panel

'''               ''
    main script
''               '''

def main(dev, args: list[str]):
    opts, terms = parse_args(args)
    if opts['invalid']: return

    terms = valid_input(SEARCH_PROMPT, "", SEARCH_TEST, default=terms)
    if opts['exact']: terms = ['@' + term if term[0] != '@' else term for term in terms]

    client = RPCClient(dev)

    try:
        selected = search_select(client.list, terms, opts['all'])
        if not selected: print("Didn't select anything")

        if opts['gui']:
            control_panel(client.list, selected)
        else:
            input_call_output(selected, opts['arg'], opts['peek'])

    # User just wanted to exit, do so peacefully
    except InputQuit: return

'''             ''
    parse args
''             '''
ALL_MODES = ['peek', 'gui', 'all', 'exact', 'help']
def parse_args(args: list[str]) -> tuple[dict, list[str]]:
    opts = {'peek': False, 'gui': False, 'all': False, 'exact': False,
            'invalid': False, 'arg': None}
    search_terms = []

    for arg in args:
        if arg.startswith('--'):
            if arg[2:] in ALL_MODES: opts[arg[2:]] = True
            else:
                print("Invalid flag: " + arg)
                opts['invalid'] = True
        elif arg.startswith('-'):
            for char in arg[1:]:
                for mode in ALL_MODES:
                    if char == mode[0]:
                        opts[mode] = True
                        break
                else:
                    print("Invalid flag: " + arg)
                    opts['invalid'] = True
        else:
            try: opts['arg'] = float(arg)
            except ValueError: search_terms.append(arg)

    return opts, search_terms

'''                    ''
    RPC search/select
''                    '''
def search_select(full_list: RPCList, terms: list[str], star: bool) -> RPCList:
    matched = full_list.search(terms)
    matched.print()

    if matched.empty():
        print(MATCH_ERR(terms))
        return RPCList() # empty list
    else:
        return __select_input(matched, star)

def __select_input(rpclist: RPCList, star: bool=False) -> RPCList:
    if rpclist.lonely() or star: return rpclist
    return valid_input(SELECT_PROMPT, SELECT_ERR(rpclist), lambda x: __select_rpcs(rpclist, x))

def __select_rpcs(rpcs: RPCList, selection: str) -> RPCList:
    match list(selection):
        case ['/', *rest]:
            return __select_input(rpcs.search(''.join(rest).split()))
    if selection[0] == '/': # recursive case, go back to select_input with narrowed search
        return __select_input(rpcs.search(selection[1:].split(), match_any))
    elif selection == '*':
        return rpcs.pick([i for i in range(len(rpcs))])
    else:
        return rpcs.pick([int(s)-1 for s in selection.split()])

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
            arg = valid_input(ARG_PROMPT, ARG_ERR(rpc), ARG_TEST(rpc), default=cli_arg)

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

RT = TypeVar('RT')
def valid_input(input_msg: str, error_msg: str, test: Callable[[str], RT], default=None) -> RT:
    # Get input/default, try to apply test and return
    try: return test(__input(input_msg, default))

    # If that didn't work, recurse until they get it right
    except (ValueError, IndexError):
        print(error_msg, end='')
        return valid_input(input_msg, error_msg, test)

SEARCH_PROMPT = "Enter search terms: "
SEARCH_TEST = lambda t: t if t[0] is not None and type(t) is list else t.split()
MATCH_ERR = lambda t: f"Couldn't find {t[0] if len(t)==1 else 'a match'}."

SELECT_PROMPT = "Select rpc, or /[search] to keep searching: "
SELECT_ERR = lambda l: f"Invalid. Select a number from 1 to {len(l)}.\n"

ARG_PROMPT = "Enter argument: "
ARG_ERR = lambda r: f"Invalid. Argument should be of {str(r.arg_type)[1:-1]}.\n"
ARG_TEST = lambda r: lambda x: r.arg_type(x) if x not in {'-', ''} else None

CURRENT_VAL_MSG = lambda a, v: f"Previously: {v}" if a is not None else f"Currently: {v}"
HELP_MSG = """
RUI - Rpc User Interface for easy control of Twinleaf devices
rui [flags] [search terms] [argument], in any order

FLAGS:
    --peek (-p) will just check the value of RPCs without prompting to change
    --all (-a) will select all matched RPCs
    --exact (-e) will search for exact strings instead of fuzzy-searching
    --gui (-g) will open the slider interface instead of calling RPCs from command line
        - "rui gui ..." also works
"""
