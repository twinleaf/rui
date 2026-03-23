import os, sys, platform

class RuiConfigs():
    """ Interface with cache file to store min and max values for RUI GUI sliders """
    def __init__(self, dev_name):
        self.dev_name = dev_name
        self.rpc_configs = dict()
        self.rpc_configs.setdefault("rpc_names", [])
        self.rpc_configs.setdefault("rpc_min", [])
        self.rpc_configs.setdefault("rpc_max", [])
        self._instantiate_rpc_sliders()

    def _update_dict(self, name, min, max):
        if not name in self.rpc_configs["rpc_names"]:
            self.rpc_configs["rpc_names"].append(name)
            self.rpc_configs["rpc_min"].append(min)
            self.rpc_configs["rpc_max"].append(max)
        else:
            idx = list(self.rpc_configs["rpc_names"]).index(name)
            self.rpc_configs["rpc_min"][idx] = min
            self.rpc_configs["rpc_max"][idx] = max
    
    def update_displayed_rpcs(self, name, min, max):
        self._update_dict(name, min, max)
        try:
            file_path = self._cache_path()
            with open(file_path, 'w') as f:
                self._write_rpc_cache(f)
        except OSError as e:
            sys.exit(f"Something went wrong with the cache path: {e}")
        except ValueError as e:
            sys.exit(f"Invalid cache at {file_path}, consider inspecting or removing: {e}")
    
    def get_rpc_min(self, name):
        try:
            idx = list(self.rpc_configs["rpc_names"]).index(name)
        except ValueError:
            idx = None
        if idx is not None: 
            return  self.rpc_configs["rpc_min"][idx]
        else:
            return 0            

    def get_rpc_max(self, name):
        try:
            idx = list(self.rpc_configs["rpc_names"]).index(name)
        except ValueError:
            idx = None
        if idx is not None: 
            return self.rpc_configs["rpc_max"][idx]
        else:
            return 1            

    def _instantiate_rpc_sliders(self):
        try:
            try: 
                file_path = self._cache_path()
                with open(file_path, 'r') as f:
                    self._read_rpc_cache(f)
            except FileNotFoundError:
                with open(file_path, "w") as f:
                    self._write_rpc_cache(f)        
        except OSError as e:
            sys.exit(f"Something went wrong with the cache path: {e}")
        except ValueError:
            sys.exit(f"Invalid cache at {file_path}, consider inspecting or removing")

    def _read_rpc_cache(self, file):
        lines = file.readlines()
        if not lines: pass 
        for line in lines:
            name, min, max = line.strip().split(' ')
            self._update_dict(name, min, max)

    def _write_rpc_cache(self, file):
        for rpc_name in self.rpc_configs["rpc_names"]:
            idx = list(self.rpc_configs["rpc_names"]).index(rpc_name)
            file.write(f"{rpc_name} {self.rpc_configs["rpc_min"][idx]} {self.rpc_configs["rpc_max"][idx]}\n")
    
    def _cache_path(self):
        if platform.system() == "Linux":
            cache_dir = os.path.expanduser("~/.cache/rui")
        elif platform.system() == "Darwin":
            cache_dir = os.path.expanduser("~/Library/Caches/rui")
        elif platform.system() == "Windows":
            cache_dir = os.path.expanduser("~\\AppData\\Local")
        else:
            cache_dir = input("Couldn't determine where to look for cache, input cache directory path: ")
        os.makedirs(cache_dir, exist_ok=True)

        base_name = f"{self.dev_name}.minmax"
        return os.path.join(cache_dir, base_name)
