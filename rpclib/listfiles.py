import os, sys
from .rpc import RPC, RPCList
from .rpctypes import TYPES_DICT
from .tio import send_request

'''                             ''
    ~/.rpc-lists r/w interface
''                             '''

class DeviceError(Exception): pass
class DaemonListError(Exception): pass
REGEN_MSG = lambda x: f"Re-generating {os.path.basename(x)} ..."
NOFILE_MSG = lambda x: f"{os.path.basename(x)} not found, generating..."

def rpclist_from_file(dirname: str, regen: bool=False) -> RPCList:
    os.makedirs(dirname, exist_ok=True)
    try:
        filepath = __get_gen_file(dirname, regen)
    except DeviceError:
        sys.exit("Device not found, exiting")
    except DaemonListError:
        sys.exit("Daemon failed to generate list, exiting")
    with open(filepath, 'r') as f:
        return RPCList([__line_to_rpc(line) for line in f.readlines()])

def __line_to_rpc(rpc_list_line: str) -> RPC:
    open_index = rpc_list_line.index('(')
    close_index = rpc_list_line.index(')')

    name = rpc_list_line[:open_index]
    type_name = rpc_list_line[open_index+1:close_index]
    arg_type = TYPES_DICT[type_name]
    return RPC(name, arg_type)

def __get_gen_file(dirname: str, regen: bool=False) -> str:
    # get name of file to write to
    try:
        devname = RPC("dev.name", None).call()
        assert type(devname) is str
    except RuntimeError:
        raise DeviceError
    filepath = os.path.join(dirname, devname + ".rpcs")

    # regenerate if necessary
    if regen or not os.path.exists(filepath):
        print(REGEN_MSG(filepath) if regen else NOFILE_MSG(filepath))
        try:
            daemon_list = send_request({'op': 'list'})
            assert type(daemon_list) is str
        except RuntimeError:
            raise DaemonListError

        with open(filepath, 'w') as f:
            f.write(daemon_list+'\n')

    # return where to get what we just wrote
    return filepath
