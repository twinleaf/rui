import os, sys
from rui.lib.cli import rpcCLI, valid_input, InputQuit
from rui.lib.rpc import RPC, RPCList, get_dev_list, rpc_type
from rui.gui import slider

'''               ''
    main script
''               '''

def main(dev, args: list[str]):
    try:
        cli         = rpcCLI(args)
        full_list   = get_dev_list(dev)

        selected    = search_select(cli, full_list)
        if not selected: 
            print("Didn't select anything")

        if cli.slider(): 
            slider(full_list, selected)
        else: 
            input_call_output(cli, selected)

    # User just wanted to exit, do so peacefully
    except InputQuit: return

def search_select(cli: rpcCLI, full_list: RPCList) -> RPCList:
    matched = full_list.search(cli.terms())
    matched.print()

    if matched.empty():
        terms = cli.terms()
        print(f"Couldn't find {terms[0] if len(terms)==1 else 'a match'}.")
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
    elif selection == '*':
        return rpcs.pick([i for i in range(len(rpcs))])
    else:
        return rpcs.pick([int(s)-1 for s in selection.split()])

def input_call_output(cli: rpcCLI, selected: RPCList):
    for rpc in selected:
        if len(selected) > 1: print(rpc)    # print where we are in call list
        arg = __print_get_arg(rpc, cli)     # ask user for argument to rpc
        output = rpc.call(arg)              # make call
        print("Reply:", output)             # print current value

def __print_get_arg(rpc: RPC, cli: rpcCLI) -> rpc_type:
    if cli.dash() or rpc.arg_type == None: return None
    print("Previously:" if cli.default_arg is not None else "Currently:", rpc.call())
    return valid_input("Enter argument: ",
                       f"Invalid. Argument should be of {str(rpc.arg_type)[1:-1]}.\n",
                       lambda x: rpc.arg_type(x) if x not in {'-', ''} else None,
                       default=cli.default_arg)
