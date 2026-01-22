class TestRPC:
    def __init__(self, string: str, dt: type, value=0):
        self.string = string
        self.type = dt
        self.value = value

    def call(self, arg=None):
        if arg is None: 
            return self.value
        else: 
            if arg == 444:
                raise RuntimeError
            self.value = self.type(arg)
            return self.value

class TestSurvey:
    def __init__(self, string: str):
        self.string = string

    def get_path(self, string):
        path = string.split('.')
        parent = self
        for survey in path[:-1]: 
            try:
                parent = getattr(parent, survey)
            except AttributeError:
                parent.add_survey(survey)
                parent = getattr(parent, survey)
        return parent, path[-1]

    def add_survey(self, path: str):
        parent, child = self.get_path(path)
        survey = TestSurvey(child)
        setattr(parent, child, survey)

    def add_rpc(self, path: str, dt: type, value=0):
        parent, child = self.get_path(path)
        rpc = TestRPC(child, dt, value)
        setattr(parent, child, rpc.call)

class TestDevice:
    def __init__(self):
        self.settings = TestSurvey("settings")
        self.settings.add_rpc("dev.name", str, value=b"TEST")
        self.settings.add_rpc("mode.autostart", int)
        self.settings.add_rpc("pump.lock.control.Kp", float)
