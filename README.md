# RUI: Rpc User Interface
RUI is a multitool for controlling Twinleaf board RPCs, featuring fuzzy searching RPC names for easy command line use and a slider GUI popup.

# Features
RUI CLI allows the user to search for RPCs and call them through simple command line IO.
RUI GUI allows the user to select RPCs from an auto-completing dropdown (up/down arrow keys to tile through completions) and define ranges to slide their values around.

# Usage
`rui [flags] [search terms]`
RUI's default behaviour is a slider interface that launches in a popup window. Search terms, if given, will use the search/select CLI pre-populate the control panel; otherwise, it will be a blank slate to add sliders to.
- --restore will reinstate RUI GUI's previous open sliders

`rui cli [flags] [search terms] [argument], in any order`
For terminal input, use RUI CLI, which asks for search terms to select one or more RPCs, and then prompts values to call them with.
- Without any arguments, RUI will prompt for both search terms and an argument.
- With only search terms, RUI will prompt to select an RPC from the search results, show its current value, then ask for an argument. Enter nothing, `-`, `quit`, or `exit` to not change it.
- Select multiple search results by inputting their indices separated by spaces, or select all results by inputting `*` instead of an index.
- Instead of an index, type /[search] to narrow the search further.
- Use `.` at the start of an argument to search for it at the end of RPCs (e.g. `.enable`)
- Use `.` at the end of an argument to search for it at the start of RPCs (e.g. `pump.`)
- Use `.` at the start and end of an argument to search for it in the middle of RPCs (e.g. `.control.`).
- Use `@` at the start of an argument to exact-search instead of fuzzy-search it. `.` in front of an argument will exact-search it including the `.`, so `rui .lock` will get `...control.lockrange` but not `...capture.block`.
- If only one result is found, RUI will go directly to that rpc. So `rui [exact search] [arg or -p]` is the same as `tio-tool rpc [exact rpc name] [arg or N/A]` but with less demanding syntax.

# Flags
- --peek (-p) will just check the value(s) of selected RPC(s) without prompting to change
- --all (-a) will select all matched RPCs instead of prompting for selection
- --exact (-e) will search for exact strings instead of fuzzy-searching
- --multisearch (-m) will search for RPCs that match any of the space-separated search terms
- --url and -s will specify the URL and route to look for a board at respectively

# Examples
``` bash
$ rui cuotff #(sic)
[ 1. bar.data.cutoff(float)
[ 2. imu.data.cutoff(float)
[ 3. mcutemp.data.cutoff(float)
[ 4. sync.data.cutoff(float)
[ 5. vrail.data.cutoff(float)
[ Select rpc(s) by #, or enter terms to narrow search:
>>> 2 3 4
# GUI opens
```
``` bash
$ rui cli decim 1 --all
[ 1. bar.data.decimation(int)
[ 2. imu.data.decimation(int)
[ 3. mcutemp.data.decimation(int)
[ 4. sync.data.decimation(int)
[ 5. vrail.data.decimation(int)
[ 
[ bar.data.decimation(int)
[ Previous value: 5
[ Reply: 1
[ 
[ imu.data.decimation(int)
[ Previous value: 100
[ Reply: 1
[ 
[ mcutemp.data.decimation(int)
[ Previous value: 1
[ Reply: 1
[ 
[ sync.data.decimation(int)
[ Previous value: 1
[ Reply: 1
[ 
[ vrail.data.decimation(int)
[ Previous value: 1
[ Reply: 1
```
