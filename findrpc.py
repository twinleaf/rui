#!/home/zhao/.basevenv/bin/python
#!/usr/bin/python
import sys
from client.client import main

if __name__ == "__main__": 
    if len(sys.argv) == 1:
        main()

    elif sys.argv[1] == 'daemon':
        from daemon.daemon import RPCDaemon, TestDaemon
        try: 
            if len(sys.argv) > 2 and sys.argv[2] == 'test':
                daemon: RPCDaemon = TestDaemon()
            else:
                daemon = RPCDaemon()
            while True: daemon.server_loop()
        except (EOFError, KeyboardInterrupt):
            print("Interrupted, exiting")

    elif sys.argv[1] == 'record':
        from test.record import record
        try:
            test_name = sys.argv[2]
            sys.argv = sys.argv[2:] # shift out two argvs
            record(main, test_name)
        except IndexError:
            print("Usage: rpc record {name} [*args]")
        except (EOFError, KeyboardInterrupt):
            print("Interrupted, exiting")

    elif sys.argv[1] == 'playback':
        from test.record import list_recorded
        from test.playback import run_transcript
        for test in list_recorded():
            run_transcript(main, test)

    else:
        main()
