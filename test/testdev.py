import os

def call_test_rpc(rpc, arg: int | float | None) -> int | float | None:
    if arg is None:
        return rpc._value
    elif arg == 444: # simulate errors
        raise RuntimeError
    else:
        rpc._value = rpc._ret_type(arg)
        return rpc._value

class Rpc:
    def __init__(self, name: str, arg_type: type, ret_type: type, value=0):
        self.__name__ = name
        self._arg_type = arg_type
        self._ret_type  = ret_type
        self._value = value
        self.__call__ = lambda arg=None: call_test_rpc(self, arg)
        self.__call__.__annotations__['arg'] = arg_type

class Survey:
    def __init__(self, name: str):
        self.__name__ = name

    def _get_path(self, name: str):
        path = name.split('.')
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

    def _add_rpc(self, path: str, arg_type: type, ret_type: type, value=0):
        parent, child = self._get_path(path)
        rpc = Rpc(path, arg_type, ret_type, value)
        setattr(parent, child, rpc)

class TestDevice:
    def __init__(self):
        self.settings = Survey("settings")
        self.settings._add_rpc("dev.name", None, str, value=b"TEST")
        self.settings._add_rpc("mode.autostart", int, int)
        self.settings._add_rpc("pump.lock.control.Kp", float, float)
        self.settings._add_rpc("pump.lock.control.Ki", float, float)
        self.settings._add_rpc("zachary.lock.control.Ki", float, float)
        self.settings._add_rpc("bob.lock.control.Ki", float, float)
        self.settings._add_rpc("alice.lock.control.Ki", float, float)
        self.settings._add_rpc("chris.lock.control.Ki", float, float)
        self.settings._add_rpc("pump.therm.control.autotune.start",
                               None, None, value=b"OK")
        self.settings._add_rpc("signal.capture.size", None, int, value=8)
        self.settings._add_rpc("signal.capture.trigger", None, None, value=8)
        self.settings._add_rpc("signal.capture.block", None, bytes, value=8)

        self.samples = None

    def _interact(self):
        os.execvp("zsh", ["zsh"])
