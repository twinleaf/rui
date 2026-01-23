#!/usr/bin/python
import os, sys
from rpclib.rpc import RPC, RPCList
from rpclib.rpccli import rpcCLI 
from rpclib.listfiles import rpclist_from_file
from rpclib.rpcio import select_input, arg_input
from gui import slider

MATCH_ERR = lambda x: f"Couldn't find {x[0] if len(x) == 1 else 'a match'}."
def find_targets(all_rpcs: RPCList, cli: rpcCLI) -> RPCList:
    ''' fuzzy search all_rpcs for cli.terms or input and update all_rpcs '''
    matched = all_rpcs.search(cli.terms(), cli.any())
    if matched.empty():
        print(MATCH_ERR(cli.terms()))
        sys.exit(1)
    return matched

def print_get_arg(rpc: RPC, cli: rpcCLI) -> int | float | None:
    ''' print current rpc value and ask user for what to change it to if any '''
    if cli.dash() or rpc.arg_type == type(None): return None 
    print("Previously:" if cli.rpc_arg is not None else "Currently:", rpc.value())
    return arg_input(rpc, cli.rpc_arg)

def input_call_output(selected_rpcs: RPCList, cli: rpcCLI):
    ''' loop through call list '''
    if cli.slider(): slider(selected_rpcs, fork=not cli.debug())
    for rpc in selected_rpcs:
        if len(selected_rpcs) > 1: print(rpc)   # print where we are in call list
        while True:                             # loop for possible + mode
            arg = print_get_arg(rpc, cli)           # ask user for argument to rpc
            output = rpc.call(arg)                  # make call
            if len(output) > 1: print(output)       # print if not just newline
            if cli.plus(): continue                 # keep looping if + mode
            else: break
        print()                                 # spacer

def find_and_select(full_list: RPCList, cli: rpcCLI) -> RPCList:
    matched   = find_targets(full_list, cli)
    selected  = select_input(matched, cli.star(), cli.slash())
    return selected

if __name__ == "__main__":
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
