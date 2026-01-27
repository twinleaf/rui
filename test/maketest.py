import pexpect
from approvaltest import verify
from pathlib import Path

def run_transcript(cli, transcript):
    child = pexpect.spawn(cli, encoding="utf-8")
    output = []

    for line in transcript.splitlines(keepends=True):
        if line.startswith("> "):
            child.send(line[2:])
        else:
            child.expect_exact(line)
            output.append(line)

    child.expect(pexpect.EOF)
    output.append(child.before)
    return "".join(output)

def test_happy_path():
    transcript = Path("tests/approvals/happy_path.transcript").read_text()
    output = run_transcript("rpc", transcript)
    verify(output)
