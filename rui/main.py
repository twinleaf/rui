import os, sys
from rui.lib.cli import rpcCLI, InputQuit
from rui.lib.rpc import RPC, get_dev_list
from rui.lib.io_methods import search_select_loop, input_call_output_loop
from rui.gui import slider

'''               ''
    main script
''               '''

def main(dev, args: list[str]):
    try:
        ''' load args and list '''
        cli         = rpcCLI(args)
        full_list   = get_dev_list(dev)

        selected = search_select_loop(cli, full_list)
        if not selected: print("Didn't select anything")

        ''' invoke gui '''
        if cli.slider():
            return slider(full_list, selected)

        ''' normal input call output loop '''
        input_call_output_loop(cli, selected)

    # User just wanted to exit, do so peacefully
    except InputQuit: return
