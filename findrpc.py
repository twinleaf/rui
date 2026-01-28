#!/home/zhao/.basevenv/bin/python
#!/usr/bin/python
import os, sys
from client.client import main

if __name__ == "__main__": 
    if len(sys.argv) == 1:
        main()

    elif sys.argv[1] == 'daemon':
        from daemon.daemon import RPCDaemon
        from test.testdev import TestDevice
        # TODO: kill existing daemon if there is one
        # actually just see what happens when you try to make two
        try: 
            if len(sys.argv) > 2 and sys.argv[2] == 'test':
                daemon = RPCDaemon(TestDevice)
            else:
                daemon = RPCDaemon(twinleaf.Device)

            daemon.server_loop()

        except (EOFError, KeyboardInterrupt):
            print("Interrupted, exiting")

    elif sys.argv[1] == 'record':
        from test.record import record
        # TODO: make fresh daemon
        # TODO: what if i want to test saving state b/w rpc calls w/i a daemon?
        try:
            sys.argv = sys.argv[1:] # only need to shift one argv
            record(main)
        except (EOFError, KeyboardInterrupt):
            print("Interrupted, exiting")

    elif sys.argv[1] == 'playback':
        # TODO: playback also needs fresh daemon
        from test.record import list_recorded
        from test.playback import run_transcript
        for test in list_recorded():
            run_transcript(main, test)

    else:
        main()
