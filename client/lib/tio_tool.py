import subprocess
from rpclib.rpclib import rpc_arg_type, rpc_ret_type

'''                      ''
    rust tool interface
''                      '''
# TODO: make test shell interface
def tio_tool_rpc(name: str, arg_type: type | None, arg: rpc_arg_type) -> rpc_ret_type:
    argv = ['rpc', '--']
    argv.append(name)
    if arg is not None: argv.append(str(arg)) # only here do we convert to str
    result = tio_tool(argv)

    for line in result.splitlines():
        words = line.split()
        match words[0]:
            case 'Reply:':
                reply = words[1]
                if reply[0] == '"': reply = reply[1:-1] # trim quotes
                # convert manually here; ret type might be non-None even if arg type None
                if arg_type is not None: reply = arg_type(reply)
                return reply
            case 'Unknown': # assuming string since no -T/-t
                continue
            case 'OK': # if this is all we get, we'll go to the return 'OK' at the end
                continue
            case 'RPC': # should be "RPC failed: [reason]"
                raise RuntimeError(name + ' | ' + line)
            case _:
                raise NotImplementedError("Don't know what to do with " + line)
    return 'OK'

CHAR_TO_TYPE = {'f': 'float', 'i': 'int', 'u': 'int',
                's': ''} # string return type means no arg type
def tio_tool_list() -> str:
    result = tio_tool(['rpc-list']).splitlines()
    file_lines = []
    for line in result:
        prefix, rest = line.split()
        if rest[:3] == "rpc": return

        open_index = rest.index('(')
        name, char = rest[:open_index], rest[open_index+1]

        if "W" in prefix:
            file_lines.append(name + '(' + CHAR_TO_TYPE(char) + ')')
        elif prefix == "???":
            file_lines.append(name + '(bytes)')
        elif prefix == "---" or prefix == "R--":
            file_lines.append(name + '()')
        else:
            raise NotImplementedError("Don't know what to do with " + line)
    return '\n'.join(file_lines)

def tio_tool(args: list[str]) -> str:
    try:
        argv = ['tio-tool'] + args
        process = subprocess.Popen(argv, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

    # For some reason tio-tool throws this on fail sometimes
    except TypeError: raise RuntimeError("tio-tool failure")
    if stderr: raise RuntimeError(stderr.strip())

    return stdout.strip()
