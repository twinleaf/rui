from tio import tio_tool 
DATA_ERR = lambda x: f"unknown data type: {x}"
RPC_ERR = "rpc call failed"
TYPES_DICT = {'f': float, 'u': int, 'i': int, 's': str, ')': None}

class RPC:
    ''' Represents a single RPC, supporting name, data type, and calling'''
    def __init__(self, name: str, type_ext: str='()'):
        self.name, self.type_ext = name, type_ext
        data_char = type_ext[1] # first char after open paren
        try: self.data_type = TYPES_DICT[data_char] 
        except KeyError: raise TypeError(DATA_ERR(data_char))

    def input_to_arg(self, x):
        return str(self.data_type(x)) if x!='-' else None

    def call(self, arg: str | None=None) -> str: 
        result = tio_tool('rpc', self.name, arg)
        lines = result.splitlines()
        return '\n'.join([line for line in lines if line.split()[0] not in {'Unknown', 'OK'}])

    def value(self): #-> self.data_type
        word = self.call().split()[1] # second word of first line
        if word[0] == '"': word = word[1:]
        if word[-1] == '"': word = word[:-1]
        return self.data_type(word)

    def __len__(self): return len(self.name)
    def __str__(self): return self.name + self.type_ext
    def __getitem__(self, key): return self.name[key]
    def __contains__(self, item): return item in self.name
