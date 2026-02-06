from __future__ import annotations
from difflib import get_close_matches

rpc_type = int | float | str | bytes | None
def type_name(t: type | None): return t.__name__ if t is not None else ''

class RPC:
    ''' Interface for an RPC, supporting name, calling, type, and search '''
    def __init__(self, name: str, func: callable, 
                 arg_type: type | None, ret_type: type | None):
        self.name, self.func = name, func
        self.arg_type, self.ret_type = arg_type, ret_type

    # throws AssertionError, TypeError
    def call(self, arg: rpc_arg_type=None) -> rpc_ret_type:
        if self.arg_type is None: assert arg is None
        value = self.func() if arg is None else self.func(self.arg_type(arg))

        if type(value) is float: value = round(value, 2)
        if type(value) is bytes: value = value.decode()
        return value

    def value(self) -> rpc_ret_type:
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

    def search(self, terms: list[str], match_any: bool) -> RPCList:
        selector = any if match_any else all
        sieve = lambda x: selector(self.fuzzy_match(term, x) for term in terms)
        return self.filter(sieve)

    def print(self):
        if len(self) == 0: return
        if len(self) == 1: print(self[0])
        else:
            for i in range(len(self)):
                print(f"{i+1}.", self[i])

    def fuzzy_match(self, search_for: str, search_in: str) -> bool:
        if search_for[0] == '/': search_for = search_for[1:] # ignore /
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
