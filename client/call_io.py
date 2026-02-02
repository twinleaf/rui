from client.cli import rpcCLI, valid_input
from client.rpc import RPC, RPCList
from rpclib.rpclib import rpc_arg_type

DASH_PLUS_ERR = "Plus (continuous input) and dash (no argument) modes incompatible, exiting"
def input_call_output_loop(cli: rpcCLI, selected: RPCList):
    ''' ask user to call '''
    for rpc in selected:
        if len(selected) > 1: print(rpc)    # print where we are in call list
        while True:                         # loop for possible + mode
            arg = print_get_arg(rpc, cli)       # ask user for argument to rpc
            output = rpc.call(arg)              # make call
            print("Reply:", output)             # print current value
            if cli.plus():                      # keep looping if + mode
                if not cli.dash(): continue     # unless dash, which is incompatible
                else: print(DASH_PLUS_ERR)
            break                         # TODO: what to do if + mode but multiple rpcs?

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
