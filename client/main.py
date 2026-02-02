# TODO: add spacers
import os, sys
from client.listfiles import rpclist_from_file
from client.cli import rpcCLI, InputQuit
from client.gui import slider

from client.search_select import search_select_loop
from client.call_io import input_call_output_loop

from rpclib.rpclib import rpc_arg_type

'''               ''
    main script
''               '''

def main(args: list[str]):
    try:
        ''' load list '''
        # first get our arguments
        cli         = rpcCLI(args)

        # load from our list directory, fetching dev.name() to know what list to load
        dirname     = os.path.expanduser("~/.rpc-lists/")
        full_list   = rpclist_from_file(dirname, cli.regen())

        selected = search_select_loop(cli, full_list)
        if not selected: print("Didn't select anything")

        ''' invoke gui '''
        if cli.slider():
            return slider(full_list, selected, fork=not cli.debug())

        ''' normal input call output loop '''
        input_call_output_loop(cli, selected)

    # User just wanted to exit, do so peacefully
    except InputQuit:
        return
