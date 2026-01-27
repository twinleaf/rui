import sys
from pathlib import Path

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

        if exc_type:
            print("Exception:", exc_type.__name__)
            print(traceback)

test_dir = Path(__file__).resolve().parent # location of this script
dest_dir = test_dir / "recorded"
dest_dir.mkdir(exist_ok=True)
def list_recorded():
    return dest_dir.iterdir()

def record(program, test_name):
    transcript_path = dest_dir / f"{test_name}.transcript"

    with Recorder(transcript_path) as recorder:
        # first write arguments
        argv = "$ [" + " ".join(sys.argv[1:]) + "]\n"
        recorder.write(argv)

        # now do whatever we're testing
        program()

    print("-- Recorded to", transcript_path, "--")
