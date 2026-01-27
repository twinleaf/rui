import sys
import pexpect
from pathlib import Path

test_name = sys.argv[2]

dest = Path("test/tests")
dest.mkdir(parents=True, exist_ok=True)
transcript_file = dest / f"{test_name}.transcript"

child = pexpect.spawn("~/twinleaf/projects/findrpc/findrpc.py", encoding="utf-8")
child.logfile = sys.stdout

buffer = []
child.logfile_read = buffer.append

try:
    while True:
        child.expect(".+", timeout=None)
except pexpect.EOF:
    pass

transcript = "".join(buffer)
transcript_file.write_text(transcript)

print(f"\nRecorded to {transcript_file}")
