import json
from .tio import shell_rpc, daemon_rpc, ProxyError, DaemonError
DATA_ERR = lambda x: f"Unknown data type: {x}"
TYPES_DICT = {'f': float, 'u': int, 'i': int, 's': str, ')': None}

class RPC:
    ''' Represents a single RPC, supporting name, data type, and calling'''
    def __init__(self, name: str, type_ext: str='()'):
        self.name, self.type_ext = name, type_ext
        data_char = type_ext[1] # first char after open paren
        try: 
            self.data_type = TYPES_DICT[data_char] 
        except KeyError: 
            raise TypeError(DATA_ERR(data_char))

    def call(self, arg: str | None=None) -> str: 
        try:
            return daemon_rpc(self.name, arg)
        except ConnectionRefusedError:
            # TODO: background daemon yourself
            print("Server not found, try starting it?")
        except DaemonError:
            print("Error in daemon loop")
        except ProxyError:
            print("Using shell rpc")
        # only get here if error
        return shell_rpc(self.name, arg)

    def value(self): #-> self.data_type
        word = self.call().split()[1] # second word of first line
        if word[0] == '"': word = word[1:]
        if word[-1] == '"': word = word[:-1]
        value = self.data_type(word)
        self.value_cache = value
        return value

    def __len__(self): return len(self.name)
    def __str__(self): return self.name + self.type_ext
    def __getitem__(self, key): return self.name[key]
    def __contains__(self, item): return item in self.name
