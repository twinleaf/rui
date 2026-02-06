from rui.lib.cli import rpcCLI, valid_input
from rui.lib.rpc import RPC, RPCList, rpc_type

MATCH_ERR = lambda terms: f"Couldn't find {terms[0] if len(terms)==1 else 'a match'}."
def search_select_loop(cli: rpcCLI, full_list: RPCList) -> RPCList:
    selected = RPCList() # start with empty list
    while True:
        if cli.terms()[0] == '\\':  break   # backslash exits search

        # cli.terms() gets search terms to filter full_list for
        matched = full_list.search(cli.terms(), cli.any())

        # didn't match anything, try again if we're in slash search
        if matched.empty():
            print(MATCH_ERR(cli.terms()))
            if cli.slash():
                cli.reset_search()
                continue
            else:
                break

        # select which rpcs to call
        next_selection = __select_input(matched, cli.star(), cli.any())
        selected += next_selection

        if not cli.slash():         break
        if next_selection.empty():  break   # backslash here exits as well
        cli.reset_search()

    return selected

def __select_input(rpclist: RPCList, star: bool=False, match_any: bool=False) -> RPCList:
    ''' recursive loop to select a full call list of rpcs '''

    # print here so we print every slash search
    rpclist.print()

    # sometimes we can just return what we have
    if rpclist.lonely() or star: return rpclist

    # otherwise do input loop
    else: return valid_input("Select rpc, or /[search] to keep searching: ",
                             f"Invalid. Select a number from 1 to {len(rpclist)}.\n",
                             lambda x: __select_rpcs(rpclist, x, match_any))

def __select_rpcs(rpcs: RPCList, selection: str, match_any: bool=False) -> RPCList:
    ''' helper for recursive __select_input function'''

    if selection == '\\':   # slash search base case, empty list
        return RPCList()
    if selection[0] == '/': # recursive case, go back to select_input with narrowed search
        return __select_input(rpcs.search(selection.split(), match_any))

    if selection == '*':    # star mode - no recusion, select everything
        return rpcs.pick([i for i in range(len(rpcs))])
    else:                   # no modes, just select by numbers
        return rpcs.pick([int(s)-1 for s in selection.split()])

DASH_PLUS_ERR = "Plus (continuous input) and dash (no argument) modes incompatible, exiting"
def input_call_output_loop(cli: rpcCLI, selected: RPCList):
    ''' ask user to call '''
    for rpc in selected:
        if len(selected) > 1: print(rpc)    # print where we are in call list
        while True:                         # loop for possible + mode
            arg = __print_get_arg(rpc, cli)       # ask user for argument to rpc
            output = rpc.call(arg)              # make call
            print("Reply:", output)             # print current value
            if cli.plus():                      # keep looping if + mode
                if not cli.dash(): continue     # unless dash, which is incompatible
                else: print(DASH_PLUS_ERR)
            break                         # TODO: what to do if + mode but multiple rpcs?

def __print_get_arg(rpc: RPC, cli: rpcCLI) -> rpc_type:
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
