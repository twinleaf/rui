import sys
from pathlib import Path

class Recorder:
    ''' Logs stdin and stdout to transcript files before redirecting back to terminal '''
    def __init__(self, transcript_dir: Path):
        self.temp_path = transcript_dir / 'tmp'

    def write_transcript(self, data: str=None):
        if data: self.transcript.write(data)
        self.transcript.flush()
    def write_stdout(self, data: str=None):
        if data: self.stdout.write(data)
        self.stdout.flush()

    def __enter__(self):
        self.transcript = open(self.temp_path, 'w')

        self.stdin = sys.stdin
        sys.stdin = self
        self.stdout = sys.stdout
        sys.stdout = self

        return self

    def readline(self):
        data = self.stdin.readline()
        # backslash tells last line not to expect newline
        self.write_transcript("\\\n> " + data)
        return data

    def write(self, data: str):
        self.write_stdout(data)
        self.write_transcript(data)

    def __exit__(self, exc_type, exc_value, traceback):
        # flush
        self.write_transcript()
        self.write_stdout()

        self.transcript.close()
        sys.stdout = self.stdout
        sys.stdin = self.stdin

        if exc_type: 
            # If we had an error, remove tmp transcript and propagate exception
            print("Exception caught, not recording")
            if self.temp_path.exists(): self.temp_path.unlink()
            return False
        else:
            print() #spacer
            while not (test_name := input("Recorded, enter test name: ")): pass

            new_transcript_path = f"{test_name}.transcript"
            self.temp_path.rename(dest_dir / new_transcript_path)

            print("-- Recorded to", new_transcript_path, "--")

test_dir = Path(__file__).resolve().parent # location of this script
dest_dir = test_dir / "recorded"
dest_dir.mkdir(exist_ok=True)
def list_recorded() -> list[Path]:
    return dest_dir.iterdir()

def record(program, args: list[str]=[]):
    with Recorder(dest_dir) as recorder:
        # first write arguments
        arg_line = "$ [" + " ".join(args) + "]\n"
        recorder.write(arg_line)

        # now do whatever we're testing
        program(args)
