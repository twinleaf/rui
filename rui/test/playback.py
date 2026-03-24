import sys, time
from pathlib import Path
from .record import list_recorded

class Playback:
    ''' Sends stdin from transcript, reads stdout and asserts against transcript '''
    def __init__(self, transcript_path: Path, silent: bool):
        self.transcript_path = transcript_path
        self.silent = silent
        self.write_buffer = ""
        self.passed = True

    def println(self, data: str):
        # we can't use print() because we own stdout, this also helps debug newlines
        if not self.silent:
            data = data.replace('\n', '\\n')
            data += '\n'
            self.stdout.write(data)
            self.stdout.flush()

    def __enter__(self):
        self.transcript = open(self.transcript_path, 'r')

        # get I/O streams
        self.stdin = sys.stdin
        sys.stdin = self
        self.stdout = sys.stdout
        sys.stdout = self

        return self

    def parse_args(self) -> list[str]:
        arg_line = self.transcript.readline()
        if arg_line[:3] != "$ [" or arg_line[-2:] != "]\n":
            self.println("Transcript doesn't start with $ [argv], instead got " + arg_line)
            self.passed = False
            raise IOError
        else:
            self.println(arg_line[:-1])
            return arg_line[3:-2].split()

    def check_write_buffer(self):
        # get data from write buffer, reset write buffer
        data, self.write_buffer = self.write_buffer, ""

        next_line = self.transcript.readline()

        # line ending with \ means no newline there
        if next_line[-2:] == "\\\n": next_line = next_line[:-2]

        # we're writing, so transcript line shouldn't be input
        if next_line[:2] == "> ":
            self.println("Expected input, instead got " + data)
            self.passed = False
        elif next_line != data:
            self.println("Expected " + next_line + ", instead got " + data)
            self.passed = False
        else:
            self.println(next_line[:-1])

    def readline(self):
        # last write finished with no newline, check write first
        if self.write_buffer: self.check_write_buffer()

        next_line = self.transcript.readline()

        # make sure transcript line is input, then pass it to our program
        if next_line[:2] != "> ":
            self.println("Expected " + next_line + ", instead asked for input")
            self.passed = False
        else:
            self.println(next_line[:-1])
            return next_line[2:]

    def write(self, data: str):
        if not data: return # stdout likes to write nothing sometimes
        else: self.write_buffer += data

        if data[-1] != '\n': return # incomplete write, don't check yet
        else: self.check_write_buffer()

    def __exit__(self, exc_type, exc_value, traceback):
        self.transcript.close()
        sys.stdout = self.stdout
        sys.stdin = self.stdin

        if exc_type: return False # propagate exception

def run_transcript(program,
                   transcript_path: Path,
                   default_args: list[str],
                   silent: bool=False
                   ) -> int:
    if not silent: print("-- Testing", transcript_path, "--")
    try:
        with Playback(transcript_path, silent) as playback:
            sys.argv = [''] +  default_args + playback.parse_args()
            program()
            status = "-- PASSED --" if playback.passed else "!!!! FAILED !!!!"
            passed = playback.passed
    except BaseException as e:
        if not silent: print(e)
        status, passed = "!!!! FAILED !!!!", False
    if not silent: print(status+'\n')
    return passed

def playback(program, default_args: list[str]=[]):
    num_passed = 0
    for test in list_recorded():
        passed = run_transcript(program, test, default_args)
        num_passed += int(passed)
    print(f"RESULTS: PASSED {num_passed} OUT OF {len(list_recorded())}")
