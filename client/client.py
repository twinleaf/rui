import os, sys
from rpclib.rpc import RPC, RPCList
from rpclib.rpccli import rpcCLI, valid_input
from rpclib.listfiles import rpclist_from_file
from rpclib.rpctypes import rpc_arg_type
from .gui import slider

'''               ''
    main script 
''               '''
def find_and_select(full_list: RPCList, cli: rpcCLI) -> RPCList:
    ''' search through rpcs and select call list '''
    matched   = _find_targets(full_list, cli)
    if matched.empty():
        sys.exit(f"Couldn't find {cli.terms()[0] if len(cli.terms()) == 1 else 'a match'}.")
    selected  = _select_input(matched, cli.star(), cli.slash())
    return selected

def input_call_output(selected_rpcs: RPCList, cli: rpcCLI):
    ''' loop through call list '''
    if cli.slider(): 
        all_numeric = True
        for rpc in selected_rpcs:
            if rpc.arg_type not in {int, float}:
                print(f"{rpc} has type {rpc.arg_type}, can't make a slider")
                all_numeric = False
        if all_numeric: 
            slider(selected_rpcs, fork=not cli.debug())

    else:
        for rpc in selected_rpcs:
            if len(selected_rpcs) > 1: print(rpc)   # print where we are in call list
            while True:                             # loop for possible + mode
                arg = _print_get_arg(rpc, cli)           # ask user for argument to rpc
                output = rpc.call(arg)                  # make call
                print("Reply:", output)                 # print current value
                if cli.plus(): 
                    print()                             # spacer
                    continue                            # keep looping if + mode
                else: break

def main():
    ''' load, search, select, and call '''
    dirname     = os.path.expanduser("~/.rpc-lists/")
    cli_args    = sys.argv[1:]
    cli         = rpcCLI(cli_args)
    full_list   = rpclist_from_file(dirname, cli.regen())
    selected    = find_and_select(full_list, cli)
    while cli.slash():
        cli.search_terms = []
        if cli.terms()[0] == '\\': break # \ during search
        next_selection = find_and_select(full_list, cli)
        if next_selection.empty(): break # \ during select
        selected += next_selection
    input_call_output(selected, cli)

'''                      ''
    main script methods
''                      '''
def __select_rpcs(rpcs: RPCList, selection: str, match_any: bool=False) -> RPCList:
    ''' helper to parse _select_input input '''
    if selection == '\\': return RPCList() # slash search base case, empty list
    if selection[0] == '/':
        # narrow search by recursively calling _select_input
        return _select_input(rpcs.search(selection.split(), match_any))
    elif selection == '*':
        return rpcs.pick([i for i in range(len(rpcs))]) # pick all
    elif len(selection.split()) == 1:
        return rpcs.pick([int(selection)-1])
    else:
        return rpcs.pick([int(s)-1 for s in selection.split()])

def _select_input(rpclist: RPCList, star: bool=False, slash: bool=False) -> RPCList:
    ''' recursive loop to select a full call list of rpcs '''
    rpclist.print()
    if rpclist.lonely() or star: return rpclist
    else: return valid_input("Select rpc, or /[search] to keep searching: ",
                             f"Invalid. Select a number from 1 to {len(rpclist)}.\n",
                             lambda x: __select_rpcs(rpclist, x, slash))

def _find_targets(all_rpcs: RPCList, cli: rpcCLI) -> RPCList:
    ''' fuzzy search all_rpcs for cli.terms or input and update all_rpcs '''
    matched = all_rpcs.search(cli.terms(), cli.any())
    return matched

def _print_get_arg(rpc: RPC, cli: rpcCLI) -> rpc_arg_type:
    ''' print current rpc value and ask user for what to change it to if any '''
    if cli.dash() or rpc.arg_type == None: return None 
    print("Previously:" if cli.default_arg is not None else "Currently:", rpc.call())
    return valid_input("Enter argument: ", 
                       f"Invalid. Argument should be of {str(rpc.arg_type)[1:-1]}.\n", 
                       lambda x: rpc.arg_type(x) if x not in {'-', ''} else None, 
                       default=cli.default_arg)
