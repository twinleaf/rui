from twinleaf import _Rpc, _rpc_type

class RPC:
    """Interface for an RPC, supporting name, calling, type, and search"""

    def __init__(self, client,  name: str, arg_type: type, ret_type: type):
        self._client, self.name = client, name
        self.arg_type, self.ret_type = arg_type, ret_type

    @classmethod
    def from_node(cls, client, node: _Rpc):
        name = node.__name__
        arg_type = node._type if node._writable else None
        ret_type = node._type
        return cls(client, name, arg_type, ret_type)

    def call(self, arg: _rpc_type = None) -> _rpc_type:
        return self._client._call_by_name(self.name, self.to_arg_type(arg))

    def to_arg_type(self, arg: _rpc_type) -> _rpc_type:
        if arg in {None, ""}:
            return None
        else:
            return self.arg_type(arg)

    def is_numeric(self) -> bool:
        return self.arg_type in {int, float} and self.ret_type in {int, float}

    def __repr__(self):
        base_str = self.name + "()"
        if self.arg_type is not None:
            base_str = base_str[:-1] + self.arg_type.__name__ + ')'
        return base_str

    def __len__(self):
        return len(self.name)

    def __getitem__(self, key):
        return self.name[key]

    def __contains__(self, item):
        return item in self.name
