# TODO: add spacers
import os, sys
from rpclib.rpc import RPC, RPCList
from rpclib.listfiles import rpclist_from_file
from rpclib.rpctypes import rpc_arg_type
from .cli import rpcCLI, valid_input, InputQuit
from .gui import slider

def select_input(rpclist: RPCList, star: bool=False, match_any: bool=False) -> RPCList:
    ''' recursive loop to select a full call list of rpcs '''

    # print here so we print every slash search
    rpclist.print()

    # sometimes we can just return what we have
    if rpclist.lonely() or star: return rpclist

    # otherwise do input loop
    else: return valid_input("Select rpc, or /[search] to keep searching: ",
                             f"Invalid. Select a number from 1 to {len(rpclist)}.\n",
                             lambda x: select_rpcs(rpclist, x, match_any))

def select_rpcs(rpcs: RPCList, selection: str, match_any: bool=False) -> RPCList:
    ''' helper for recursive select_input function'''

    if selection == '\\':   # slash search base case, empty list
        return RPCList()
    if selection[0] == '/': # recursive case, go back to select_input with narrowed search
        return select_input(rpcs.search(selection.split(), match_any))

    if selection == '*':    # star mode - no recusion, select everything
        return rpcs.pick([i for i in range(len(rpcs))])
    else:                   # no modes, just select by numbers
        return rpcs.pick([int(s)-1 for s in selection.split()])

def print_get_arg(rpc: RPC, cli: rpcCLI) -> rpc_arg_type:
    ''' print current rpc value and ask user for what to change it to if any '''

    # if we can't set a value, we don't need this function
    if cli.dash() or rpc.arg_type == None: return None

    # print current value, we use Previously if the cli already has a new value in mind
    print("Previously:" if cli.default_arg is not None else "Currently:", rpc.call())

    # try cli's value if it exists, otherwise input loop to match rpc.arg_type
    return valid_input("Enter argument: ",
                       f"Invalid. Argument should be of {str(rpc.arg_type)[1:-1]}.\n",
                       lambda x: rpc.arg_type(x) if x not in {'-', ''} else None,
                       default=cli.default_arg)

'''               ''
    main script
''               '''

MATCH_ERR = lambda terms: f"Couldn't find {terms[0] if len(terms)==1 else 'a match'}."

def main(args: list[str]):
    try:
        ''' load list '''
        # first get our arguments
        cli         = rpcCLI(args)

        # load from our list directory, fetching dev.name() to know what list to load
        dirname     = os.path.expanduser("~/.rpc-lists/")
        full_list   = rpclist_from_file(dirname, cli.regen())
        selected = RPCList()

        ''' search & select loop '''
        while True: # only runs once unless we're slash search
            if cli.terms()[0] == '\\':  break   # backslash exits search

            # cli.terms() gets search terms to filter full_list for
            matched = full_list.search(cli.terms(), cli.any())

            # didn't match anything, try again if we're in slash search
            if matched.empty():
                print(MATCH_ERR(cli.terms()))
                if cli.slash(): continue

            # ask which rpcs to call
            next_selection = select_input(matched, cli.star(), cli.any())
            selected += next_selection

            if not cli.slash():         break
            if next_selection.empty():  break   # backslash here exits as well
            cli.search_terms = []               # reset search terms
        # if selected is empty as this point, remaining code will do nothing

        ''' invoke gui '''
        if cli.slider():
            # if we want sliders, we have to check if we can make them
            non_numeric = RPCList([r for r in selected if r.arg_type not in {int, float}])
            numeric = RPCList([r for r in selected if r.arg_type in {int, float}])
            for rpc in non_numeric: print(f"{rpc} has type {rpc.arg_type}, can't make a slider")

            # see which rpcs we need to watch out for changes behind our backs
            for rpc in numeric:
                rpc.check_is_sample()

            # okay, make sliders
            if numeric:
                slider(numeric, full_list, fork=not cli.debug())

            return # don't go to call loop, even if we didn't make a gui


        ''' normal input call output loop '''
        for rpc in selected:
            if len(selected) > 1: print(rpc)    # print where we are in call list
            while True:                         # loop for possible + mode
                arg = print_get_arg(rpc, cli)       # ask user for argument to rpc
                output = rpc.call(arg)              # make call
                print("Reply:", output)             # print current value
                if cli.plus():                      # keep looping if + mode
                    if not cli.dash():              # unless dash, which is incompatible
                        continue
                break

    # User just wanted to exit, do so peacefully
    except InputQuit:
        pass
