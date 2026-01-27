import sys
from pathlib import Path

class Playback:
    ''' Sends stdin from transcript, reads stdout and asserts against transcript '''
    def __init__(self, transcript_path):
        self.transcript_path = transcript_path
        self.write_buffer = ""
        self.passed = True

    def println(self, data: str):
        # we can't use print() because we own stdout, this also helps debug newlines
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

    def parse_argv(self):
        argv = self.transcript.readline()
        if argv[:3] != "$ [" or argv[-2:] != "]\n":
            self.println("Transcript doesn't start with $ [argv], instead got " + argv)
            self.passed = False
            raise IOError
        else: 
            sys.argv = [""] + argv[3:-2].split()

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

    def readline(self):
        # last write finished with no newline, check write first
        if self.write_buffer: self.check_write_buffer()

        next_line = self.transcript.readline()

        # make sure transcript line is input, then pass it to our program
        if next_line[:2] != "> ":
            self.println("Expected " + next_line + ", instead asked for input")
            self.passed = False
        return next_line[2:]

    def write(self, data):
        if not data: return # stdout likes to write nothing sometimes
        else: self.write_buffer += data

        if data[-1] != '\n': return # incomplete write, don't check yet
        else: self.check_write_buffer()

    def __exit__(self, exc_type, exc_value, traceback):
        self.transcript.close()
        sys.stdout = self.stdout
        sys.stdin = self.stdin

        if exc_type:
            print("Exception:", exc_type.__name__)
            print(traceback)

def run_transcript(program, transcript_path):
    print("-- Testing", transcript_path, "--")
    sys.argv = [""]
    with Playback(transcript_path) as playback:
        # set sys.argv to be what we want
        playback.parse_argv()

        # now do whatever we're testing
        program()
        status = "-- PASSED --" if playback.passed else "-- FAILED --"
    print(status)
