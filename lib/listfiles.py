import os, sys
from .rpclist import RPCList
from .rpc import RPC
from .tio import tio_tool

def rpclist_from_file(dirname: str, regen: bool=False) -> RPCList:
    os.makedirs(dirname, exist_ok=True)
    filepath = __get_gen_file(dirname, regen)
    with open(filepath, 'r') as f:
        return RPCList([__line_to_rpc(line) for line in f.readlines()])

def __line_to_rpc(rpc_list_line: str) -> RPC:
    base_string = rpc_list_line.split()[1] # ignore RWP
    open_index = base_string.index('(')
    close_index = base_string.index(')')

    name = base_string[:open_index]
    ext = base_string[open_index:]
    return RPC(name, ext)

DEV_ERR = "Device not found"
RPCLIST_ERR = "tio-tool rpc-list failed"
REGEN_MSG = lambda x: f"Re-generating {os.path.basename(x)} ..."
NOFILE_MSG = lambda x: f"{os.path.basename(x)} not found, generating..."

def __get_gen_file(dirname: str, regen: bool=False) -> str:
    try: 
        devname = RPC("dev.name", "(string)").value()
    except RuntimeError: 
        sys.exit(DEV_ERR)
    filepath = os.path.join(dirname, devname + ".rpcs")
    if regen or not os.path.exists(filepath):
        __gen_msg(filepath, regen)
        __generate_list(filepath)
    return filepath

def __gen_msg(filepath, regen):
    print(REGEN_MSG(filepath) if regen else NOFILE_MSG(filepath))

def __generate_list(filepath: str):
    try: rpc_list = tio_tool("rpc-list")
    except RuntimeError: sys.exit(RPCLIST_ERR)
    str_list = [line + '\n' for line in rpc_list.splitlines()]
    with open(filepath, 'w') as f: f.writelines(str_list)
