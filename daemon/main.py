import os, sys, subprocess
from daemon.daemon import RPCDaemon
from test.testdev import TestDevice

def main(args: list[str]):
    if 'test' not in args:
        import twinleaf
        dev_constructor = twinleaf.Device
    else:
        dev_constructor = TestDevice

    override = '--override' in args
    silent = '--silent' in args
    thread = '--thread' in args

    if thread:
        spawn_thread_daemon([a for a in args if a != '--thread'])

    else:
        with RPCDaemon(dev_constructor, override, silent) as daemon:
            daemon.server_loop()

def spawn_thread_daemon(args: list[str]) -> subprocess.Popen:
    # Slightly evil recursive import for other relative imports to work
    rui_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rui_script = os.path.join(rui_dir, 'rui.py')

    with open(os.devnull, 'w') as devnull:
         process = subprocess.Popen(
            [sys.executable, rui_script, 'daemon'] + args,
            stdout=devnull, stderr=devnull,
            close_fds=True, start_new_session=True)
    return process
