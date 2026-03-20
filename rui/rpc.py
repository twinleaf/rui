from __future__ import annotations
from inspect import getmembers, signature
from typing import Callable
from enum import Enum, auto
from difflib import get_close_matches

rpc_type = int | float | str | bytes | None
PROXY_FATAL = "FATAL: Device proxy failed"
def RPC_ERROR(e=''): return f"ERROR: {e}"
def type_name(t: type | None): return t.__name__ if t is not None else ''
class MatchResult(Enum):
    NONE = 0,
    EXACT = 1,
    FUZZY = 2,

class RPCClient:
    ''' Calls RPCs while handling device-level tasks like proxy errors '''
    def __init__(self, device):
        self._device = device
        nodes = rpc_dfs(device.settings)
        self.dict = {node.__name__: node for node in nodes}
        self.list = RPCList([RPC.from_node(self, node) for node in nodes])

    def call_by_name(self, name: str, arg: rpc_type=None) -> rpc_type:
        try:
            rpc = self.dict[name]
            if arg is None:
                value = rpc.__call__()
            else:
                value = rpc.__call__(arg)
            if type(value) is float: value = round(value, 2)
            if type(value) is bytes: value = value.decode() # TODO: what about real bytes rpcs
            return value

        except KeyError:
            if self.dict:
                return RPC_ERROR(f"RPC {name} does not exist")
            else: # RPC isn't in our dict because we don't have a dict!
                try:
                    self._device.reinit()
                    self.__init__(self._device)
                    return self.call_by_name(name, arg)
                except:
                    return PROXY_FATAL

        # rpc.__call__ failed
        except RuntimeError as e:
            if self.validate_device():
                return RPC_ERROR(e)
            else:
                try:
                    self._device.reinit()
                    self.__init__(self._device)
                    return self.call_by_name(name, arg)
                except:
                    return PROXY_FATAL

    def validate_device(self) -> bool:
        # Test our device connection by calling a universal RPC
        # If it fails
        try:
            self.dict["dev.name"].__call__()
        except RuntimeError:
            self.reset_device()
            return False
        else:
            return True

    def reset_device(self):
        self.dict = {}
        self.list = RPCList()

class RPC:
    ''' Interface for an RPC, supporting name, calling, type, and search '''
    def __init__(self, client: RPCClient, name: str, arg_type: type, ret_type: type):
        self._client, self.name = client, name
        self.arg_type, self.ret_type = arg_type, ret_type

    @classmethod
    def from_node(cls, client: RPCClient, node: "twinleaf.rpc"):
        name = node.__name__
        sig = signature(node.__call__)
        ret_type = sig.return_annotation

        params = sig.parameters
        try:
            arg_type = params['arg'].annotation
            if arg_type == int | None: arg_type = int
            if arg_type == float | None: arg_type = float
            if arg_type == str | None: arg_type = str
        except KeyError:
            arg_type = None
        arg_type = arg_type
        return cls(client, name, arg_type, ret_type)

    def call(self, arg: rpc_type=None) -> rpc_type:
        return self._client.call_by_name(self.name, arg)
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

    def search(self, terms: list[str], exact: bool=False, match_any: bool=False) -> RPCList:
        a = any if match_any else all
        if exact:
            terms = ['@' + term if not term.startswith('@') else term for term in terms]
        exact = lambda x: a(self.fuzzy_match(term, x) == MatchResult.EXACT for term in terms)
        fuzzy = lambda x: a(self.fuzzy_match(term, x) != MatchResult.NONE for term in terms)
        return self.filter(exact) or self.filter(fuzzy)

    def print(self):
        if len(self) == 0: return
        if len(self) == 1: print(self[0])
        else:
            for i in range(len(self)):
                print(f"{i+1}.", self[i])

    def fuzzy_match(self, term: str, name: str) -> MatchResult:
        if not term:
            return MatchResult.NONE
        if term == '.':
            return MatchResult.EXACT
        elif term[0] == '@' and term[1:]:
            return MatchResult.EXACT if term[1:] in name else MatchResult.NONE

        if '.' in term:
            subterms = [t for t in term.split('.') if t]
            if all(self.fuzzy_match(t, name) == MatchResult.EXACT for t in subterms):
                return MatchResult.EXACT
            elif all(self.fuzzy_match(t, name) == MatchResult.FUZZY for t in subterms):
                return MatchResult.FUZZY
            else:
                return MatchResult.NONE
        else:
            substrings = []
            for word in name.split('.'):
                if len(word) < len(term):
                    substrings += [word]
                else:
                    substrings += [word[i:i+len(term)] for i in range(len(word)-len(term)+1)]

        if term in substrings:
            return MatchResult.EXACT
        else:
            chars_per_mistake = 4 # match 'ferq' to 'freq' but not 'fer' to 'fre'
            cutoff = 1 - 1/chars_per_mistake # 0.75
            if get_close_matches(term, substrings, cutoff=cutoff):
                return MatchResult.FUZZY
            else:
                return MatchResult.NONE

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

