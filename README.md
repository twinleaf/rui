# RUI: Rpc User Interface
RUI is a multitool for controlling Twinleaf board RPCs, featuring fuzzy searching RPC names for easy command line use and a slider GUI popup.

# Installation
```bash
git clone git@code.twinleaf.com:zhao/rui.git
cd rui
./install.sh
rui --help
```

# Features
RUI CLI allows the user to search for RPCs and call them through simple command line IO.
RUI GUI allows the user to select RPCs from an auto-completing dropdown (up/down arrow keys to tile through completions) and define ranges to slide their values around.

# Usage
`rui gui [flags] [search terms]`
Launch the RUI GUI in a pop-up window. Search terms, if given, will use the search/select CLI pre-populate the control panel; otherwise, it will be a blank slate to add sliders to.

`rui [flags] [search terms] [argument], in any order`
RUI's default behaviour is RUI CLI, which asks for search terms to select one or more RPCs, and then prompts values to call them with.
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
$ rui septoint --peek #(sic)
> 1. cell.therm.control.setpoint(float)
> 2. probe.therm.control.setpoint(float)
> 3. pump.therm.control.setpoint(float)
>
> Select rpc(s) by #, or enter terms to narrow search:
>>> 2
>
> Reply: 60.0
```
``` bash
$ rui pump.setpoint
> pump.therm.control.setpoint(float)
> Current value: 60.0
> Enter argument:
>>> 68
> Reply: 60.0
```
``` bash
$ rui decim 1 --all
> 1. field.data.decimation(int)
> 2. vector.data.decimation(int)
> 3. vectorcal.data.decimation(int)
> 4. status.data.decimation(int)
> 5. aux.data.decimation(int)
> 6. therm.data.decimation(int)
>
> field.data.decimation(int)
> Previous value: 1
> Reply: 1
>
> vector.data.decimation(int)
> Previous value: 1
> Reply: 1
>
> vectorcal.data.decimation(int)
> Previous value: 100
> Reply: 1
>
> status.data.decimation(int)
> Previous value: 100
> Reply: 1
>
> aux.data.decimation(int)
> Previous value: 100
> Reply: 1
>
> therm.data.decimation(int)
> Previous value: 5
> Reply: 1
```
``` bash
$ rui gui probe control
> 1. probe.therm.control.Kd(float)
> 2. probe.therm.control.Ki(float)
> 3. probe.therm.control.Kp(float)
> 4. probe.therm.control.enable(int)
> 5. probe.therm.control.lingertime(float)
> 6. probe.therm.control.locklevel(float)
> 7. probe.therm.control.manual(int)
> 8. probe.therm.control.reset()
> 9. probe.therm.control.searchrate(float)
> 10. probe.therm.control.setpoint(float)
> 11. probe.therm.control.unlocktime(float)
> Select rpc(s) by #, or enter terms to narrow search:
>>> 1 2 3 4 6 10
--- slider popup ----
```
