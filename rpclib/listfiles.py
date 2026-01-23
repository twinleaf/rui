import os, sys
from .rpc import RPC, RPCList
from .tio import daemon_shell_list
from .rpctypes import TYPES_DICT

'''                             ''
    ~/.rpc-lists r/w interface
''                             '''

DEV_ERR = "Device not found"
RPCLIST_ERR = "tio-tool rpc-list failed"
REGEN_MSG = lambda x: f"Re-generating {os.path.basename(x)} ..."
NOFILE_MSG = lambda x: f"{os.path.basename(x)} not found, generating..."

def rpclist_from_file(dirname: str, regen: bool=False) -> RPCList:
    os.makedirs(dirname, exist_ok=True)
    filepath = __get_gen_file(dirname, regen)
    with open(filepath, 'r') as f:
        return RPCList([__line_to_rpc(line) for line in f.readlines()])

def __line_to_rpc(rpc_list_line: str) -> RPC:
    open_index = rpc_list_line.index('(')
    close_index = rpc_list_line.index(')')

    name = rpc_list_line[:open_index]
    arg_type = TYPES_DICT[rpc_list_line[open_index+1]]
    return RPC(name, arg_type)

# TODO: figure out these runtime errors
def __get_gen_file(dirname: str, regen: bool=False) -> str:
    # get name of file to write to
    try: 
        devname = RPC("dev.name", None).call()
        assert type(devname) is str
    except RuntimeError: 
        sys.exit(DEV_ERR)
    filepath = os.path.join(dirname, devname + ".rpcs")

    # regenerate if necessary
    if regen or not os.path.exists(filepath):
        print(REGEN_MSG(filepath) if regen else NOFILE_MSG(filepath))
        try: 
            rpc_list: list[str] = daemon_shell_list()
        except RuntimeError: 
            sys.exit(RPCLIST_ERR)

        with open(filepath, 'w') as f: 
            f.write('\n'.join(rpc_list))

    # return where to get what we just wrote
    return filepath
