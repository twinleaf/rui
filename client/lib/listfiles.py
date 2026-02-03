import os
from client.lib.rpc import RPC, RPCList
from client.lib.send_request import send_request
from rpclib.rpclib import TYPES_DICT

'''                             ''
    ~/.rpc-lists r/w interface
''                             '''

def get_rpclist(dirname: str, regen: bool=False) -> RPCList:
    try: devname = RPC("dev.name", None).call()
    except RuntimeError: raise SystemExit("Device not found, exiting")
    filepath = os.path.join(dirname, devname + ".rpcs")

    # Get list from daemon if we have it
    try:
        daemon_list = send_request({'op': 'list'})

        # Save it to file before returning
        with open(filepath, 'w') as f: f.write(daemon_list+'\n')

        return RPCList([__line_to_rpc(line) for line in daemon_list.split()])

    # TODO: test this
    # If that fails, read from file
    except (RuntimeError, ConnectionResetError):
        if regen or not os.path.exists(filepath):
            print("Re-generating {os.path.basename(filepath)}")
            with open(filepath, 'w') as f: f.write(tio_tool_list()+'\n')

        with open(filepath, 'r') as f:
            return RPCList([__line_to_rpc(line) for line in f.readlines()])
    #except ConnectionResetError:
    #    return get_rpclist(dirname, regen) # Connection resets sometimes, just try again

def __line_to_rpc(rpc_list_line: str) -> RPC:
    open_index = rpc_list_line.index('(')
    close_index = rpc_list_line.index(')')

    name = rpc_list_line[:open_index]
    type_name = rpc_list_line[open_index+1:close_index]
    arg_type = TYPES_DICT[type_name]
    return RPC(name, arg_type)
