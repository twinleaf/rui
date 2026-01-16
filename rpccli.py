from typing import Any
from rpcio import search_input
ALL_MODES = {'-', '+', '++', '*', '@', '|', 'debug', 'regen'}

class rpcCLI:
    '''Interface to parse and store command line input to findrpc'''
    def __init__(self, argv: list[str]):
        self.search_terms:  list[str] = []      # list of search terms
        self.rpc_arg:       Any       = None    # argument to call rpc with, usually numeric
        self.modes:         set[str]  = set()   # set of options from ALL_MODES
        self.__parse_args(argv)
    
    def __parse_args(self, argv: list[str]):
        for arg in argv:
            if arg in ALL_MODES: 
                self.add_mode(arg)
            else: 
                try: 
                    # assume numeric datatype
                    self.rpc_arg = str(float(arg)) if '.' in arg else str(int(arg))
                except ValueError: self.search_terms.append(arg)

    def terms(self) -> list[str]: 
        terms = search_input(self.search_terms)
        if self.exact(): terms = ['@' + term for term in terms]
        self.search_terms = terms
        return terms

    def add_mode(self, mode: str): self.modes.add(mode)
    def any(self) -> bool: return '|' in self.modes # match any search term instead of all
    def star(self) -> bool: return '*' in self.modes # select all rpcs
    def dash(self) -> bool: return '-' in self.modes # no argument
    def plus(self) -> bool: return '+' in self.modes # loop calls forever
    def slider(self) -> bool: return '++' in self.modes #Qt slider
    def exact(self) -> bool: return '@' in self.modes # exact instead of fuzzy match
    def regen(self) -> bool: return 'regen' in self.modes # regenerate rpc-list file
    def debug(self) -> bool: return 'debug' in self.modes # debug options
