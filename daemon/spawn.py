import os, sys, time, threading, subprocess
from daemon.daemon import RPCDaemon
# TODO: spawn permanent daemon with subprocess

class TempDaemon(RPCDaemon):
    ''' Thread daemon bound to stop_signal so it can be killed by main '''
    def __init__(self, dev_constructor, stop_signal: threading.Event):
        # Shouldn't need to override, but want silent daemon for testing
        super().__init__(dev_constructor, server_override=False, silent=True)
        self.stop_signal    = stop_signal

    def server_loop(self, silent=False):
        self._make_server()

        self.server.settimeout(0.3)
        while not self.stop_signal.is_set():
            try:
                client, _ = self.server.accept() # raise error if no immediate client
                client_thread = threading.Thread(target=self._handle_client,
                                        args=(client,), daemon=True)
                client_thread.start()
            except TimeoutError:
                assert self._still_connected()
        # exit gracefully now that stop signal has been received

def make_temp_daemon(dev_constructor, stop_signal):
    with TempDaemon(dev_constructor, stop_signal) as daemon:
        daemon.server_loop()

def spawn_test_daemon(dev_constructor, override=False, silent=False) -> threading.Event:
    stop_signal = threading.Event()
    daemon_thread = threading.Thread(target=make_temp_daemon,
                                     args=(dev_constructor, stop_signal),
                                     daemon=False) # don't forcekill on parent death
    daemon_thread.start()
    time.sleep(0.1)
    return stop_signal
    
def spawn_permanent_daemon(dev_constructor, override=False, silent=False):
    pass
