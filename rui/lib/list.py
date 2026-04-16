from __future__ import annotations

from typing import Callable
from difflib import get_close_matches
from enum import Enum, auto


class RPCList:
    """List class with filtering methods"""

    def __init__(self, rpcs: list[RPC] = []):
        self.list = rpcs

    def filter(self, cond: Callable[[str], bool]) -> RPCList:
        return RPCList([rpc for rpc in self if cond(rpc.name)])

    def pick(self, indices: list[int]) -> RPCList:
        return RPCList([self[i] for i in indices])

    def search(
        self, terms: list[str], exact: bool = False, match_any: bool = False
    ) -> RPCList:
        a = any if match_any else all
        if exact:
            terms = ["@" + term if not term.startswith("@") else term for term in terms]
        exact = lambda x: a(
            self.fuzzy_match(term, x) == MatchResult.EXACT for term in terms
        )
        fuzzy = lambda x: a(
            self.fuzzy_match(term, x) != MatchResult.NONE for term in terms
        )
        return self.filter(exact) or self.filter(fuzzy)

    def print(self):
        if len(self) == 0:
            return
        if len(self) == 1:
            print(self[0])
        else:
            for i in range(len(self)):
                print(f"{i + 1}.", self[i])

    def fuzzy_match(self, term: str, name: str) -> MatchResult:
        if not term:
            return MatchResult.NONE
        if term == ".":
            return MatchResult.EXACT
        elif term[0] == "@" and term[1:]:
            return MatchResult.EXACT if term[1:] in name else MatchResult.NONE

        if "." in term:
            subterms = [t for t in term.split(".") if t]
            if all(self.fuzzy_match(t, name) == MatchResult.EXACT for t in subterms):
                return MatchResult.EXACT
            elif all(self.fuzzy_match(t, name) == MatchResult.FUZZY for t in subterms):
                return MatchResult.FUZZY
            else:
                return MatchResult.NONE
        else:
            substrings = []
            for word in name.split("."):
                if len(word) < len(term):
                    substrings += [word]
                else:
                    substrings += [
                        word[i : i + len(term)]
                        for i in range(len(word) - len(term) + 1)
                    ]

        if term in substrings:
            return MatchResult.EXACT
        else:
            chars_per_mistake = 4  # match 'ferq' to 'freq' but not 'fer' to 'fre'
            cutoff = 1 - 1 / chars_per_mistake  # 0.75
            if get_close_matches(term, substrings, cutoff=cutoff):
                return MatchResult.FUZZY
            else:
                return MatchResult.NONE

    def empty(self):
        return len(self) == 0

    def lonely(self):
        return len(self) <= 1

    def __len__(self):
        return len(self.list)

    def __repr__(self):
        return str([str(rpc) for rpc in self.list])

    def __iter__(self):
        return self.list.__iter__()

    def __next__(self):
        return self.list.__next__()

    def __getitem__(self, key):
        return self.list[key]

    def __contains__(self, item):
        return item in self.list

    def __plus__(self, other):
        return RPCList(self.list + other.list)

    def __iadd__(self, other):
        return RPCList(self.list + other.list)


class MatchResult(Enum):
    NONE = (0,)
    EXACT = (1,)
    FUZZY = (2,)
