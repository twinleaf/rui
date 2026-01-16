import os
from rpc import RPC 
from tio import tio_tool

class RPCList:
    ''' Mutable list class that diminishes as you search & select '''
    def __init__(self, dirname: str, regen: bool=False):
        filepath = _get_gen_file(dirname, regen)
        with open(filepath, 'r') as f:
            self.list = [_line_to_rpc(line) for line in f.readlines()]

    def search(self, search_terms: list[str]):
        self.list = [rpc for rpc in self if 
                     all(_fuzzy_match(term, rpc.name) for term in search_terms)]

    def select(self, x: str) -> bool: # returns True if done searching else False
        if x[0] == '/': 
            self.list = [rpc for rpc in self if _fuzzy_match(x, rpc.name)]
            return False
        if x == '*':            
            self.list = self.list
        elif len(x.split()) == 1: 
            self.list = [self[int(x)-1]]
        else:                   
            self.list = [self[int(x)-1] for x in x.split()]
        return True

    def print(self, spacer: bool=False):
        if spacer: print()
        if len(self) == 1: 
            print(self[0])
        else:
            for i in range(len(self)): 
                print(f"{i+1}.", self[i])
            print() #spacer

    def empty(self): return len(self) == 0
    def single(self): return len(self) == 1
    def __len__(self): return len(self.list)
    def __iter__(self): return self.list.__iter__()
    def __next__(self): return self.list.__next__()
    def __getitem__(self, key): return self.list[key]
    def __contains__(self, item): return item in self.list

def _line_to_rpc(rpc_list_line: str) -> RPC:
    base_string = rpc_list_line.split()[1] # ignore RWP
    open_index = base_string.index('(')
    close_index = base_string.index(')')

    name = base_string[:open_index]
    ext = base_string[open_index:]
    return RPC(name, ext)

'''                      ''
    rpc list helpers
''                      '''
import os, sys
DEV_ERR = "Device not found"
RPCLIST_ERR = "tio-tool rpc-list failed"
REGEN_MSG = lambda x: f"Re-generating {os.path.basename(x)} ..."
NOFILE_MSG = lambda x: f"{os.path.basename(x)} not found, generating..."

def _get_gen_file(dirname: str, regen: bool=False) -> str:
    try: devname = RPC("dev.name", "(string)").value()
    except RuntimeError: sys.exit(DEV_ERR)
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

from difflib import get_close_matches
def _fuzzy_match(search_for: str, search_in: str) -> bool:
    if search_for[0] == '/': search_for = search_for[1:] # ignore /
    if search_for[0] == '@': return search_for[1:] in search_in
    if search_for[0] == '.': return search_for in search_in

    st = search_for.replace('.', '..')  # be less forgiving with matching dots
    name = search_in.replace('.', '..')
    substrings = [name[i:i+len(st)] for i in range(len(name)-len(st)+1)]

    chars_per_mistake = 4            # match 'ferq' to 'freq' but not 'fer' to 'fre'
    cutoff = 1 - 1/chars_per_mistake # 0.75
    return get_close_matches(st, substrings, cutoff=cutoff) != []
