import os, sys
from rui.lib.listfiles import get_rpclist
from rui.lib.search_select import search_select_loop
from rui.lib.call_io import input_call_output_loop

from rui.lib.cli import rpcCLI, InputQuit
from rui.gui import slider

'''               ''
    main script
''               '''

def main(dev, args: list[str]):
    try:
        ''' load args and list '''
        cli         = rpcCLI(args)
        full_list   = get_rpclist(dev)

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
