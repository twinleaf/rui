from rui.lib.cli import rpcCLI, valid_input
from rui.lib.rpc import RPC, RPCList, rpc_type

MATCH_ERR = lambda terms: f"Couldn't find {terms[0] if len(terms)==1 else 'a match'}."
def search_select(cli: rpcCLI, full_list: RPCList) -> RPCList:
    matched = full_list.search(cli.terms())
    matched.print()

    if matched.empty():
        print(MATCH_ERR(cli.terms()))
        return RPCList() # empty list
    else:
        return __select_input(matched, cli.star())

def __select_input(rpclist: RPCList, star: bool=False) -> RPCList:
    if rpclist.lonely() or star: return rpclist
    return valid_input("Select rpc, or /[search] to keep searching: ",
                         f"Invalid. Select a number from 1 to {len(rpclist)}.\n",
                         lambda x: __select_rpcs(rpclist, x))

def __select_rpcs(rpcs: RPCList, selection: str, match_any: bool=False) -> RPCList:
    ''' pick rpcs or recurse to __select_input if we keep searching '''

    if selection[0] == '/': # recursive case, go back to select_input with narrowed search
        return __select_input(rpcs.search(selection[1:].split(), match_any))
    elif selection == '*':  # star mode, select everything
        return rpcs.pick([i for i in range(len(rpcs))])
    else:                   # no modes, just select by numbers
        return rpcs.pick([int(s)-1 for s in selection.split()])

def input_call_output(cli: rpcCLI, selected: RPCList):
    ''' ask user to call '''
    for rpc in selected:
        if len(selected) > 1: print(rpc)    # print where we are in call list
        arg = __print_get_arg(rpc, cli)     # ask user for argument to rpc
        output = rpc.call(arg)              # make call
        print("Reply:", output)             # print current value

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
