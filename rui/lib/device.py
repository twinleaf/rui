import inspect
import os
import platform
import struct
import sys

import twinleaf


class Device(twinleaf.Device):
    """Wrapper for twinleaf.Device to support some cache manipulation"""

    def __init__(self, url, route, instantiate=True):
        super().__init__(url=url, route=route, instantiate=instantiate)

    def reinit(self):
        """Create a new Device and set this object to (all but) become it"""
        self.settings.__dict__ = {}
        self.__dict__ = Device(self._url, self._route).__dict__

    def print_cache(self):
        try:
            file_path = self._cache_path()
            print(file_path)
            with open(file_path, "r") as f:
                for line in f.readlines():
                    print(line, end="")
        except OSError as e:
            print(f"Something went wrong with the cache path: {e}", file=sys.stderr)
        except RuntimeError as e:
            print(f"Couldn't connect to the board: {e}", file=sys.stderr)

    def remove_cache(self):
        try:
            file_path = self._cache_path()
            os.remove(file_path)
        except OSError as e:
            print(f"Something went wrong with the cache path: {e}", file=sys.stderr)
        except RuntimeError as e:
            print(f"Couldn't connect to the board: {e}", file=sys.stderr)

    def _cache_path(self):
        if platform.system() == "Linux":
            cache_dir = os.path.expanduser("~/.cache/twinleaf")
        elif platform.system() == "Darwin":
            cache_dir = os.path.expanduser("~/Library/Caches/twinleaf")
        else:
            raise OSError(platform.system() + " not supported for RUI cache")
        os.makedirs(cache_dir, exist_ok=True)

        dev_name = self._rpc("dev.name", b"").decode()
        rpc_hash = hex(struct.unpack("<I", self._rpc("rpc.hash", b""))[0])[2:].zfill(8)
        base_name = f"{dev_name}.{rpc_hash}.rpcs"
        return os.path.join(cache_dir, base_name)


class TestDevice:
    """Device that doesn't actually connect to any proxy"""

    def __init__(self, url, route, instantiate=True):
        self._url, self._route = url, route
        self._dead = False
        self._instantiate_test()

    def reinit(self):
        if self._dead:
            self._dead = False
        else:
            self.settings.__dict__ = {}
            self.__dict__ = TestDevice(self._url, self._route).__dict__

    def _instantiate_test(self):
        self.settings = Survey("settings")
        self.samples = None
        for rpc in self._test_rpcs():
            rpc._setup_test_rpc(self)
            self.settings._add_rpc(self, rpc)
        self._write_test_cache()

    def _test_rpcs(self):
        return [
            Rpc("dev.name", None, str, value=b".TEST"),
            Rpc("dev.port.rate", int, int, value=100000),
            Rpc("dev.port.rate.default", int, int, value=100000),
            Rpc("test.data.enable", int, int, value=0),
            Rpc("test.data.decimation", int, int, value=0),
            Rpc("test.data.cutoff", float, float, value=0),
            Rpc("sw.start", None, None, value=b""),
            Rpc("rpc.hash", None, int, value=1234567890),
            Rpc("rpc.id", bytes, bytes),
        ]

    def _die(self):
        self._dead = True

    def _call_test_rpc(self, rpc, arg: int | float | None) -> int | float | None:
        if self._dead:
            raise RuntimeError("TESTDEVICE: Device dead!")

        if arg is None:
            return rpc._value
        else:
            # simulate errors
            if arg == 404:
                raise RuntimeError("TESTDEVICE: RPC failed!")
            elif arg == 444:
                self._die()
                raise RuntimeError("TESTDEVICE: Killing device!")

            rpc._value = rpc._ret_type(arg)
            return rpc._value

    def print_cache(self):
        try:
            file_path = self._cache_path()
            print(file_path)
            with open(file_path, "r") as f:
                for line in f.readlines():
                    print(line, end="")
        except OSError as e:
            print(f"Something went wrong with the cache path: {e}", file=sys.stderr)

    def remove_cache(self):
        try:
            file_path = self._cache_path()
            os.remove(file_path)
        except OSError as e:
            print(f"Something went wrong with the cache path: {e}", file=sys.stderr)

    def _write_test_cache(self):
        try:
            file_path = self._cache_path()
            with open(file_path, "w") as f:
                f.write("RUI TestDevice cache\n")
        except OSError as e:
            print(f"Something went wrong with the cache path: {e}", file=sys.stderr)

    def _cache_path(self):
        if platform.system() == "Linux":
            cache_dir = os.path.expanduser("~/.cache/twinleaf")
        elif platform.system() == "Darwin":
            cache_dir = os.path.expanduser("~/Library/Caches/twinleaf")
        else:
            raise OSError(platform.system() + " not supported for RUI cache")
        os.makedirs(cache_dir, exist_ok=True)

        dev_name = ".TEST"
        rpc_hash = "1234567890"
        base_name = f"{dev_name}.{rpc_hash}.rpcs"
        return os.path.join(cache_dir, base_name)


class Rpc:
    """Fake dev.settings... RPC object"""

    def __init__(self, name: str, arg_type: type, ret_type: type, value=0):
        self.__name__ = name
        self._arg_type = arg_type
        self._ret_type = ret_type
        self._value = value

    def _setup_test_rpc(self, dev: TestDevice):
        self.__call__ = lambda arg=None: dev._call_test_rpc(self, arg)
        self.__call__.__annotations__["arg"] = self._arg_type
        self.__call__.__annotations__["return"] = self._ret_type


class Survey:
    """Fake dev.settings... survey object"""

    def __init__(self, name: str):
        self.__name__ = name

    def _get_path(self, name: str):
        path = name.split(".")
        parent = self
        for survey in path[:-1]:
            try:
                parent = getattr(parent, survey)
            except AttributeError:
                parent._add_survey(survey)
                parent = getattr(parent, survey)
        return parent, path[-1]

    def _add_survey(self, path: str):
        parent, child = self._get_path(path)
        survey = Survey(child)
        setattr(parent, child, survey)

    def _add_rpc(self, dev: TestDevice, rpc: Rpc):
        parent, child = self._get_path(rpc.__name__)
        setattr(parent, child, rpc)
