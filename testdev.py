# TODO: actually write tests

def call_test_rpc(rpc, arg: int | float | None) -> int | float | None:
    if arg is None: 
        return rpc._value
    elif arg == 444: # simulate errors
        raise RuntimeError
    else:
        rpc._value = rpc._ret_type(arg)
        return rpc._value

class TestRPC:
    def __init__(self, string: str, arg_type: type, ret_type: type, value=0):
        self._string = string
        self._arg_type = arg_type
        self._ret_type  = ret_type
        self._value = value
        self.__call__ = lambda arg=None: call_test_rpc(self, arg)
        self.__call__.__annotations__['arg'] = arg_type

class TestSurvey:
    def __init__(self, string: str):
        self._string = string

    def _get_path(self, string):
        path = string.split('.')
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
        survey = TestSurvey(child)
        setattr(parent, child, survey)

    def _add_rpc(self, path: str, arg_type: type, ret_type: type, value=0):
        parent, child = self._get_path(path)
        rpc = TestRPC(child, arg_type, ret_type, value)
        setattr(parent, child, rpc.__call__)

class TestDevice:
    def __init__(self):
        self.settings = TestSurvey("settings")
        self.settings._add_rpc("dev.name", type(None), str, value=b"TEST")
        self.settings._add_rpc("mode.autostart", int, int)
        self.settings._add_rpc("pump.lock.control.Kp", float, float)
        self.settings._add_rpc("pump.therm.control.autotune.start", 
                               type(None), type(None), value=b"OK")
