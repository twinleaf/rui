from client.rpc import RPCList
from client.cli import rpcCLI, valid_input

MATCH_ERR = lambda terms: f"Couldn't find {terms[0] if len(terms)==1 else 'a match'}."
def search_select_loop(cli: rpcCLI, full_list: RPCList) -> RPCList:
    selected = RPCList() # start with empty list
    while True:
        if cli.terms()[0] == '\\':  break   # backslash exits search

        # cli.terms() gets search terms to filter full_list for
        matched = full_list.search(cli.terms(), cli.any())

        # didn't match anything, try again if we're in slash search
        if matched.empty():
            print(MATCH_ERR(cli.terms()))
            if cli.slash():
                cli.reset_search()
                continue
            else:
                break

        # select which rpcs to call
        next_selection = select_input(matched, cli.star(), cli.any())
        selected += next_selection

        if not cli.slash():         break
        if next_selection.empty():  break   # backslash here exits as well
        cli.reset_search()

    return selected

def select_input(rpclist: RPCList, star: bool=False, match_any: bool=False) -> RPCList:
    ''' recursive loop to select a full call list of rpcs '''

    # print here so we print every slash search
    rpclist.print()

    # sometimes we can just return what we have
    if rpclist.lonely() or star: return rpclist

    # otherwise do input loop
    else: return valid_input("Select rpc, or /[search] to keep searching: ",
                             f"Invalid. Select a number from 1 to {len(rpclist)}.\n",
                             lambda x: select_rpcs(rpclist, x, match_any))

def select_rpcs(rpcs: RPCList, selection: str, match_any: bool=False) -> RPCList:
    ''' helper for recursive select_input function'''

    if selection == '\\':   # slash search base case, empty list
        return RPCList()
    if selection[0] == '/': # recursive case, go back to select_input with narrowed search
        return select_input(rpcs.search(selection.split(), match_any))

    if selection == '*':    # star mode - no recusion, select everything
        return rpcs.pick([i for i in range(len(rpcs))])
    else:                   # no modes, just select by numbers
        return rpcs.pick([int(s)-1 for s in selection.split()])

