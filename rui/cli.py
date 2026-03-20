from typing import Callable
from rui.rpc import RPCList, RPCClient, rpc_type

def cli(dev, args):
    client = RPCClient(dev)
    selected = search_select(client.list, args.terms, args.exact, args.all, args.multisearch)
    input_call_output(selected, args.default_arg, args.peek)

'''                         ''
    Select RPCs from list
''                         '''
def search_select(full_list: RPCList, search_terms: list[str],
                  exact: bool=False, select_all: bool=False, multisearch: bool=False
                  ) -> RPCList:
    terms = search_terms
    while not terms:
        terms = input(SEARCH_PROMPT).split(" ")
        terms = [t for t in terms if t and not t.isspace()]

    matched = full_list.search(terms, exact, multisearch)
    if matched.empty():
        print(MATCH_ERR(terms))
        return matched

    if select_all:
        matched.print()
        print() # spacer
        return matched
    else:
        return select_input(matched)

def select_input(matched: RPCList) -> RPCList:
    if matched.lonely(): 
        return matched
    else: 
        matched.print()
        while not (answer := input(SELECT_PROMPT)) or answer.isspace(): pass
        print() # spacer
        match answer:
            case '*':
                return matched
            case nums if nums and all([n.isnumeric() and 1 <= int(n) <= len(matched) for n in nums.split()]):
                return matched.pick([int(n)-1 for n in nums.split()])
            case nums if all([n.isnumeric() for n in nums.split()]):
                print(SELECT_ERR(matched))
                return select_input(matched)
            case _:
                terms = answer.split(" ")
                narrowed = matched.search(terms, match_any=True)
                if narrowed.empty():
                    print(MATCH_ERR(terms))
                    return select_input(matched)
                else:
                    return select_input(narrowed)

'''                         ''
    RPC command line calls
''                         '''
def input_call_output(selected: RPCList, cli_arg: rpc_type=None, peek: bool=False):
    for rpc in selected:
        if selected.list.index(rpc) > 0:
            print() # spacer
        print(rpc)

        # Let the user know the current/previous value
        if rpc.ret_type is bytes:
            print("Bytes RPCs not yet supported")
            continue
        elif peek or rpc.arg_type is None:
            arg = None
        else:
            current = rpc.call()
            print(CURRENT_VAL_MSG(cli_arg, current))

            # Get argument of appropriate type
            arg = cli_arg
            while cli_arg is None:
                try:
                    answer = input(ARG_PROMPT)
                    arg = rpc.arg_type(answer) if answer else None
                    break
                except ValueError:
                    print(ARG_ERR(rpc))

        # If we might be an "action" RPC, be careful
        if rpc.ret_type is None:
            if input(ACTION_PROMPT).lower() != 'y':
                print(ACTION_QUIT)
                continue

        # Make call and print new value
        output = rpc.call(arg)
        print("Reply:", output)

SEARCH_PROMPT = "Enter search terms: "
MATCH_ERR = lambda t: f"Couldn't find {t[0] if len(t)==1 else 'a match'}"

SELECT_PROMPT = "Select rpc(s) by #, or enter terms to narrow search: "
SELECT_ERR = lambda l: f"Invalid. Select number(s) from 1 to {len(l)} or enter terms to narrow search."

ARG_PROMPT = "Enter argument: "
ARG_ERR = lambda r: f"Invalid. Argument should be of {str(r.arg_type)[1:-1]}."

ACTION_PROMPT = "Send RPC? y/[n] "
ACTION_QUIT = "Not sending RPC"
CURRENT_VAL_MSG = lambda a, v: f"Previous value: {v}" if a is not None else f"Current value: {v}"
