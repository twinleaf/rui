#!/usr/bin/python
import os, sys
from rpc import RPC 
from rpclist import RPCList
from rpccli import rpcCLI 
from rpcio import select_input, arg_input
from slider import slider

MATCH_ERR = lambda x: f"Couldn't find {x[0] if len(x) == 1 else 'a match'}.\n"
def find_targets(cli: rpcCLI, all_rpcs: RPCList):
    ''' fuzzy search all_rpcs for cli.terms or input and update all_rpcs '''
    all_rpcs.search(cli.terms()) 
    if all_rpcs.empty(): 
        print(MATCH_ERR(cli.terms()), end='')
        sys.exit(1)

def input_rpc(cli: rpcCLI, found_rpcs: RPCList, spacer=False):
    ''' print rpcs, ask for selection user wants to call, and return it '''
    found_rpcs.print(spacer)
    if found_rpcs.single() or cli.star(): return 
    done = select_input(found_rpcs)
    if not done: input_rpc(cli, found_rpcs, spacer=True)

def input_arg(cli: rpcCLI, rpc: RPC): # -> rpc.data_type 
    ''' print current rpc value and ask user for what to change it to if any '''
    if cli.dash() or not rpc.data_type: return None 
    print("Previously:" if cli.rpc_arg is not None else "Currently:", rpc.value())
    return arg_input(rpc, cli.rpc_arg)

def input_call_output(cli: rpcCLI, selected_rpcs: RPCList):
    ''' loop through call list '''
    for rpc in selected_rpcs:
        print()                                 # spacer
        if len(selected_rpcs) > 1: print(rpc)   # print where we are in call list

        if cli.slider(): slider(rpc)
        else:
            while True:     # loop for possible + mode
                arg = input_arg(cli, rpc)           # ask user for argument to rpc
                output = rpc.call(arg)              # make call
                if len(output) > 1: print(output)   # print if not just newline
                if cli.plus(): continue             # keep looping if + mode
                break

if __name__ == "__main__":
    dirname     = os.path.expanduser("~/.rpc-lists/")
    cli_args    = sys.argv[1:]
    cli         = rpcCLI(cli_args)
    LIST        = RPCList(dirname, cli.regen())
    find_targets     (cli, LIST)
    input_rpc        (cli, LIST)
    input_call_output(cli, LIST)
