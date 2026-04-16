from rui.lib.rpc import RPC
from rui.lib.list import RPCList

from twinleaf import _Rpc, _RpcNode, _rpc_type

# ERRORS
PROXY_FATAL = "FATAL: Device proxy failed"
RPC_ERROR = lambda e='': f"ERROR: {e}"


class RPCClient:
    """Calls RPCs while handling device-level tasks like proxy errors"""

    def __init__(self, device):
        self._device = device
        nodes = RPCClient._rpc_dfs(device.settings)
        self.dict = {node.__name__: node for node in nodes}
        self.list = RPCList([RPC.from_node(self, node) for node in nodes])

    @staticmethod
    def _rpc_dfs(parent) -> list[_Rpc]:
        rpcs = []
        nodes = [v for v in parent.__dict__.values() if isinstance(v, _RpcNode)]
        for node in nodes:
            if isinstance(node, _Rpc):
                rpcs += [node]
            rpcs += RPCClient._rpc_dfs(node)
        return rpcs

    def _call_by_name(self, name: str, arg: _rpc_type = None) -> _rpc_type:
        try:
            rpc = self.dict[name]
            if arg is None:
                value = rpc.__call__()
            else:
                value = rpc.__call__(arg)
            if type(value) is float:
                value = round(value, 2)
            if type(value) is bytes:
                value = value.decode()  # TODO: what about real bytes rpcs
            if type(value) is str and value == "":
                value = "OK"
            return value

        except KeyError:
            if self.dict:
                return RPC_ERROR(f"RPC {name} does not exist")
            else:  # RPC isn't in our dict because we don't have a dict!
                try:
                    self._device.reinit()
                    self.__init__(self._device)
                    return self._call_by_name(name, arg)
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
                    return self._call_by_name(name, arg)
                except:
                    return PROXY_FATAL

    def dev_name(self) -> str:
        ret = self.dict["dev.name"].__call__()
        if type(ret) is bytes:
            return ret.decode()
        else:
            return ret

    def validate_device(self) -> bool:
        # Test our device connection by calling a universal RPC
        # If it fails
        try:
            self.dev_name()
        except RuntimeError:
            self._reset_device()
            return False
        else:
            return True

    def _reset_device(self):
        self.dict = {}
        self.list = RPCList()
