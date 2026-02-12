from test.record import Recorder, list_recorded
from test.playback import run_transcript
import sys
from pathlib import Path

class ReRecorder(Recorder):
    ''' Sends stdin from transcript, reads stdout and asks if it's right '''
    def __init__(self, transcript_path: Path):
        super().__init__(transcript_path.parent)
        self.transcript_path = transcript_path
        self.passed = True

    def __enter__(self):
        super().__enter__()
        self.ref_transcript = open(self.transcript_path, 'r')
        return self

    def parse_args(self) -> list[str]:
        arg_line = self.ref_transcript.readline()
        if arg_line[:3] != "$ [" or arg_line[-2:] != "]\n":
            self.write_stdout("Transcript doesn't start with $ [argv], instead got " + arg_line)
            self.passed = False
            raise IOError
        else:
            self.write_transcript(arg_line)
            self.write_stdout(arg_line)
            self.args = arg_line[3:-2].split()
            return self.args

    def readline(self):
        # Get next input line and pass it to our program
        while (next_line := self.ref_transcript.readline())[:2] != "> ":
            if not next_line:
                self.write_stdout("\nExpected input, got transcript end\n")
                self.passed = False
                raise IOError
        # backslash tells last line not to expect newline
        self.write_transcript("\\\n" + next_line)
        self.write_stdout(next_line[2:])
        return next_line[2:]

    def __exit__(self, exc_type, exc_value, traceback):
        self.write_transcript()
        self.write_stdout()
        self.transcript.close()
        self.ref_transcript.close()
        sys.stdout = self.stdout
        sys.stdin = self.stdin

        # TODO: clean up end prompt and add ability to re-record with same name/args
        if exc_type is IOError:
            answer = input("Rejected, not recording. Delete? y/[_] ")
            if answer in {'y', 'Y'} and self.transcript_path.exists():
                self.transcript_path.unlink()
            return True # silence error

        elif exc_type: # Any other exception
            print("Exception caught, not recording")
            if self.temp_path.exists(): self.temp_path.unlink()
            return False

        else: # No exception
            print() # spacer
            if input("Looks good? [y]/_ ") in {'y', 'Y', ''}:
                answer = input("Approved, rename? y/[_] ")
                if answer in {'y', 'Y'}:
                    name = input("Rename test " + self.transcript_path.name[:-11] + " to: ")
                    self.transcript_path = self.transcript_dir / ( name + ".transcript")

                print("Recording to", self.transcript_path)
                self.temp_path.rename(self.transcript_path)

            else:
                answer = input("Rejected, not recording. Delete? y/[_] ")
                if answer in {'y', 'Y'} and self.transcript_path.exists():
                    self.transcript_path.unlink()

def rerecord_transcripts(program) -> int:
    for test in list_recorded():
        passed = run_transcript(program, test, silent=True)
        if not passed:
            print("-- Re-recording", test, "--")
            try:
                with ReRecorder(test) as rerecorder:
                    args = rerecorder.parse_args()
                    program(args)
            except TypeError:
                print("Expected input, got nothing")
                print("Rejected, not recording")
        print(test.name + " passed" if passed else "")
