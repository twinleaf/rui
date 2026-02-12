import twinleaf
import os, sys, inspect, platform

class Device(twinleaf.Device):
    def __init__(self):
        super().__init__(instantiate=False)

        # Check out instantiate code
        which_instantiate = inspect.getsource(super()._instantiate_rpcs)
        if "rpc.listinfo" in which_instantiate:
            # Instantiate code would try to query RPCs, let's do that with cache instead
            self._instantiate_rpcs()
        elif "self._rpc_list()" in which_instantiate:
            # Instatiate code can call new Rust cacheing RPC list, use it
            super()._instantiate_rpcs()
        else:
            sys.exit("Don't know what device you have, check your twinleaf pip install?")

    def _instantiate_rpcs(self):
        cls = self._get_obj_survey(self)
        setattr(self, 'settings', cls())

        try:
            try:
                file_path = self._cache_path()
                with open(file_path, 'r') as f:
                    self._read_rpc_cache(f)
            except FileNotFoundError:
                with open(file_path, 'w') as f:
                    self._write_rpc_cache(f)
        except OSError as e:
            sys.exit(f"Something went wrong with the cache path: {e}")
        except RuntimeError as e:
            sys.exit(f"RPC failed: {e}")
        except ValueError as e:
            sys.exit(f"Invalid cache at {file_path}, consider inspecting or removing: {e}")

    def _read_rpc_cache(self, file):
        for line in file.readlines():
            meta, name = line.strip().split(' ')
            meta_hex = int(meta, 16)
            self._metaprogram_rpc(meta_hex, name)

    def _write_rpc_cache(self, file):
        print("Generating RPC cache.... ", end='', flush=True)
        percent=0

        n = int.from_bytes(self._rpc("rpc.listinfo", b""), "little")
        for i in range(n):
            if i / n > percent:
                print('█', end='', flush=True)
                percent += 0.02

            res = self._rpc("rpc.listinfo", i.to_bytes(2, "little"))
            meta = int.from_bytes(res[0:2], "little")
            name = res[2:].decode()
            self._metaprogram_rpc(meta, name)
            file.write(f"{hex(meta)[2:].zfill(4)} {name}\n")
        print("\nDone!")

    def _metaprogram_rpc(self, meta, name):
        parent = self.settings
        *prefix, mname = name.split('.')
        if prefix and (prefix[0] == "rpc"): prefix[0] = "_rpc"
        for token in prefix:
            if not hasattr(parent, token):
                cls = self._get_obj_survey(token)
                setattr(parent, token, cls())
            parent = getattr(parent, token)

        cls = self._get_rpc_obj(name, meta)
        setattr(parent, mname, cls())

    def _cache_path(self):
        if platform.system() == "Linux":
            cache_dir = os.path.expanduser("~/.cache/twinleaf")
        elif platform.system() == "Darwin":
            cache_dir = os.path.expanduser("~/Library/Caches/twinleaf")
        elif platform.system() == "Windows":
            cache_dir = os.path.expanduser("~\\AppData\\Local")
        else:
            cache_dir = input("Couldn't determine where to look for cache, input cache directory path: ")
        os.makedirs(cache_dir, exist_ok=True)

        dev_name = self._rpc("dev.name", b"").decode()
        rpc_hash = self._rpc("rpc.hash", b"").hex()
        base_name = f"{dev_name}.{rpc_hash}.rpcs"
        return os.path.join(cache_dir, base_name)
