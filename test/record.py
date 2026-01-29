import sys
from pathlib import Path

# TODO: actually record tests
class Recorder:
    ''' Logs stdin and stdout to transcript files before redirecting back to terminal '''
    def __init__(self, transcript_path):
        self.transcript_path = transcript_path

    def write_transcript(self, data=None):
        if data: self.transcript.write(data)
        self.transcript.flush()
    def write_stdout(self, data=None):
        if data: self.stdout.write(data)
        self.stdout.flush()

    def __enter__(self):
        self.transcript = open(self.transcript_path, 'w')

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

    def write(self, data):
        self.write_stdout(data)
        self.write_transcript(data)

    def __exit__(self, exc_type, exc_value, traceback):
        # flush
        self.write_transcript()
        self.write_stdout()

        self.transcript.close()
        sys.stdout = self.stdout
        sys.stdin = self.stdin

        if exc_type: return False # propagate exception

test_dir = Path(__file__).resolve().parent # location of this script
dest_dir = test_dir / "recorded"
dest_dir.mkdir(exist_ok=True)
def list_recorded():
    return dest_dir.iterdir()

def record(program, args=[]):
    transcript_path = dest_dir / "tmp.transcript"

    with Recorder(transcript_path) as recorder:
        # first write arguments
        arg_line = "$ [" + " ".join(args) + "]\n"
        recorder.write(arg_line)

        # now do whatever we're testing
        program(args)

    print() #spacer
    test_name = input("Recorded, enter a test name: ").replace(' ', '_')
    new_transcript_path = f"{test_name}.transcript"
    transcript_path.rename(dest_dir / new_transcript_path)
    print("-- Recorded to", new_transcript_path, "--")
