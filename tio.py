import os, sys, subprocess

'''                      ''
    rust tool interface
''                      '''

def tio_tool(tool: str, *args: str | None, test: bool=False) -> str:
    argv = ['tio-tool', tool, '--'] + [arg for arg in args if arg is not None]

    try: result = __sh(argv, test) # run in shell or test
    except FileNotFoundError: sys.exit("tio-tool not found, install or check PATH") 

    if result[1]: raise RuntimeError('\n'.join(result)) # stderr
    return result[0] #stdout

def __sh(argv: list[str], test: bool) -> tuple[str, str]:
    if not test: # run with shell
        result = subprocess.run(argv, capture_output=True)
        return __parse_result(result.stdout), __parse_result(result.stderr)

    else:        # run as test, no real device
        raise NotImplementedError

def __parse_result(result: bytes) -> str:
    return result.strip().decode('utf-8')
