from __future__ import annotations
from inspect import getmembers, signature
from typing import get_args
from difflib import get_close_matches

rpc_type = int | float | str | bytes | None
def type_name(t: type | None): return t.__name__ if t is not None else ''

class RPCClient:
    ''' Calls RPCs while handling device-level tasks like proxy errors '''
    def __init__(self, device):
        self.device = device
        self.list = RPCList([RPC(self, node) for node in rpc_dfs(device.settings)])
        self.test_rpc = RPC(self, device.settings.dev.name)

    def call(self, rpc: RPC, arg: rpc_type=None) -> rpc_type:
        try:
            if arg is None:
                value = rpc._call()
            else:
                value = rpc._call(rpc.arg_type(arg))

            if type(value) is float: value = round(value, 2)
            if type(value) is bytes and rpc.ret_type is not bytes:
                # TODO: what to do with real bytes rpcs
                value = value.decode()
            return value

        except RuntimeError as e:
            try:
                self.call(self.test_rpc)
            except RuntimeError:
                # test rpc doesn't work, we have a broken device
                pass
            else:
                # test rpc worked, our rpc just failed
                return f"ERROR: {e}"

class RPC:
    ''' Interface for an RPC, supporting name, calling, type, and search '''
    def __init__(self, client: RPCClient, node: "twinleaf.rpc"):
        self._client, self._call = client, node.__call__
        self.name = node.__name__
        sig = signature(node.__call__)
        self.ret_type = sig.return_annotation

        params = sig.parameters
        try:
            arg_type = params['arg'].annotation
            if arg_type == int | None: arg_type = int
            if arg_type == float | None: arg_type = float
            if arg_type == str | None: arg_type = str
        except KeyError:
            arg_type = None
        self.arg_type = arg_type

    def call(self, arg: rpc_arg_type=None) -> rpc_type:
        return self._client.call(self, arg)
    def value(self) -> rpc_type:
        return self.call()

    def __repr__(self): return self.name + '(' + type_name(self.arg_type) + ')'
    def __len__(self): return len(self.name)
    def __getitem__(self, key): return self.name[key]
    def __contains__(self, item): return item in self.name

class RPCList:
    ''' List class with filtering methods '''
    def __init__(self, rpcs: list[RPC]=[]):
        self.list = rpcs

    def filter(self, cond: Callable[[str], bool]) -> RPCList:
        return RPCList([rpc for rpc in self if cond(rpc.name)])
    def pick(self, indices: list[int]) -> RPCList:
        return RPCList([self[i] for i in indices])

    def search(self, terms: list[str]) -> RPCList:
        sieve = lambda x: all(self.fuzzy_match(term, x) for term in terms)
        return self.filter(sieve)

    def print(self):
        if len(self) == 0: return
        if len(self) == 1: print(self[0])
        else:
            for i in range(len(self)):
                print(f"{i+1}.", self[i])

    def fuzzy_match(self, search_for: str, search_in: str) -> bool:
        if search_for[0] == '@': return search_for[1:] in search_in
        if search_for[0] == '.': return search_for in search_in

        st = search_for.replace('.', '..')  # be less forgiving with matching dots
        name = search_in.replace('.', '..')
        substrings = [name[i:i+len(st)] for i in range(len(name)-len(st)+1)]

        chars_per_mistake = 4 # match 'ferq' to 'freq' but not 'fer' to 'fre'
        cutoff = 1 - 1/chars_per_mistake # 0.75
        return get_close_matches(st, substrings, cutoff=cutoff) != []

    def empty(self): return len(self) == 0
    def lonely(self): return len(self) <= 1
    def __len__(self): return len(self.list)
    def __repr__(self): return str([str(rpc) for rpc in self.list])
    def __iter__(self): return self.list.__iter__()
    def __next__(self): return self.list.__next__()
    def __getitem__(self, key): return self.list[key]
    def __contains__(self, item): return item in self.list
    def __plus__(self, other): return RPCList(self.list + other.list)
    def __iadd__(self, other): return RPCList(self.list + other.list)

''' dev to RPC class interface '''
def is_rpc(x): return type(x).__name__.lower() == "rpc"
def is_survey(x): return type(x).__name__.lower() == "survey"
def rpc_dfs(parent) -> list["rpc"]:
    rpcs = []
    nodes = [v for a, v in getmembers(parent) if is_rpc(v) or is_survey(v)]
    for node in nodes:
        if is_rpc(node): rpcs += [node]
        rpcs += rpc_dfs(node)
    return rpcs
