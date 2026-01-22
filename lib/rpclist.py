import os
from typing import Callable
from difflib import get_close_matches
from .rpc import RPC
from .tio import tio_tool

class RPCList:
    ''' List class with filtering methods '''
    def __init__(self, rpcs: list[RPC]=[]):
        self.list = rpcs

    def filter(self, cond: Callable[[str], bool]): # -> RPCList
        return RPCList([rpc for rpc in self if cond(rpc.name)])
    def pick(self, indices: list[int]): # -> RPCList
        return RPCList([self[i] for i in indices])

    def search(self, terms: list[str], match_any: bool): # -> RPCList
        selector = any if match_any else all
        sieve = lambda x: selector(_fuzzy_match(term, x) for term in terms)
        return self.filter(sieve)

    def print(self):
        if len(self) == 0: return
        if len(self) == 1: print(self[0])
        else:
            for i in range(len(self)): 
                print(f"{i+1}.", self[i])
            print() #spacer

    def empty(self): return len(self) == 0
    def lonely(self): return len(self) <= 1
    def __str__(self): return str([str(rpc) for rpc in self.list])
    def __len__(self): return len(self.list)
    def __iter__(self): return self.list.__iter__()
    def __next__(self): return self.list.__next__()
    def __getitem__(self, key): return self.list[key]
    def __contains__(self, item): return item in self.list
    def __plus__(self, other): return RPCList(self.list + other.list)
    def __iadd__(self, other): return RPCList(self.list + other.list)

def _fuzzy_match(search_for: str, search_in: str) -> bool:
    if search_for[0] == '/': search_for = search_for[1:] # ignore /
    if search_for[0] == '@': return search_for[1:] in search_in
    if search_for[0] == '.': return search_for in search_in

    st = search_for.replace('.', '..')  # be less forgiving with matching dots
    name = search_in.replace('.', '..')
    substrings = [name[i:i+len(st)] for i in range(len(name)-len(st)+1)]

    chars_per_mistake = 4    # match 'ferq' to 'freq' but not 'fer' to 'fre'
    cutoff = 1 - 1/chars_per_mistake # 0.75
    return get_close_matches(st, substrings, cutoff=cutoff) != []
