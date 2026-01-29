import os, sys, time, threading, subprocess
from daemon.daemon import RPCDaemon
# TODO: spawn permanent daemon with subprocess

def make_daemon(dev_constructor, override=False, silent=False):
    with RPCDaemon(dev_constructor, override) as daemon:
        daemon.get_device(silent)
        daemon.server_loop(silent)

def spawn_temp_daemon(dev_constructor, override=False, silent=False) -> threading.Thread:
    daemon_thread = threading.Thread(target=make_daemon, 
                                     args=(dev_constructor,override,silent),
                                     daemon=False) # don't forcekill on parent death
    daemon_thread.start()
    time.sleep(0.1)
    return daemon_thread
    
def spawn_permanent_daemon(dev_constructor, override=False, silent=False):
    pass
