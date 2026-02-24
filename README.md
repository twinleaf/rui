# RUI: Rpc User Interface
RUI is a multitool for controlling Twinleaf board RPCs, featuring fuzzy searching RPC names for easy command line use and a slider GUI popup.

# Installation
```bash
git clone git@code.twinleaf.com:zhao/rui.git
cd rui
source install.sh
rui --help
```

# GUI
RUI's GUI allows the user to select RPCs from an auto-completing dropdown (up/down arrow keys to tile through completions) and define ranges to slide their values around. It can be launched with the --gui flag to pre-populate with the command line-selected RPCs, or through `rui gui` for a blank slate.

# Usage
`rui gui [--url url] [-s route]`: Launch the GUI with no command line selection

`rui [flags] [search terms] [argument] [--url url] [-s route], in any order`
- Without any arguments, RUI will prompt for both search terms and an argument.
- With only search terms, RUI will prompt to select an RPC from the search results, show its current value, then ask for an argument. Enter nothing, `-`, `quit`, or `exit` to not change it.
- Select multiple search results by inputting their indices separated by spaces, or select all results by inputting `*` instead of an index.
- Instead of an index, type /[search] to narrow the search further.
- Use `@` in front of an argument to exact-search instead of fuzzy-search it. `.` in front of an argument will exact-search it including the `.`, so `rui .lock` will get `...control.lockrange` but not `...capture.block`.
- If only one result is found, RUI will go directly to that rpc. So `rui [exact search] [arg or -p]` is the same as `tio-tool rpc [exact rpc name] [arg or N/A]` but with less demanding syntax.

# Flags
- --peek (-p) will just check the value(s) of selected RPC(s) without prompting to change
- --all (-a) will select all matched RPCs instead of prompting for selection
- --exact (-e) will search for exact strings instead of fuzzy-searching
- --gui (-g) will open the slider interface instead of calling from command line.
- --url and -s will specify the URL and route to look for a board at respectively

# Examples
``` bash
$ rui septoint --peek #(sic)
> 1. probe.therm.control.setpoint(f32)
> 2. pump.therm.control.setpoint(f32)
> 3. pump.therm.control.setpoint.min(f32)
> 4. pump.lock.control.setpoint(f32)
> 5. cell.therm.control.setpoint(f32)
>
> Select rpc, or /[search] to keep searching: 
>>> 2
>
> Reply: 60.0
```
``` bash
$ rui decim 1 --all
> 1. field.data.decimation(u32)
> 2. vector.data.decimation(u32)
> 3. vectorcal.data.decimation(u32)
> 4. status.data.decimation(u32)
> 5. aux.data.decimation(u32)
> 6. therm.data.decimation(u32)
>
> field.data.decimation(u32)
> Previously: 1
> Reply: 1
>
> vector.data.decimation(u32)
> Previously: 1
> Reply: 1
>
> vectorcal.data.decimation(u32)
> Previously: 100
> Reply: 1
>
> status.data.decimation(u32)
> Previously: 100
> Reply: 1
>
> aux.data.decimation(u32)
> Previously: 100
> Reply: 1
>
> therm.data.decimation(u32)
> Previously: 5
> Reply: 1
```
``` bash
$ rui setpoint --gui
> 1. probe.therm.control.setpoint(f32)
> 2. pump.therm.control.setpoint(f32)
> 3. pump.therm.control.setpoint.min(f32)
> 4. pump.lock.control.setpoint(f32)
> 5. cell.therm.control.setpoint(f32)
>
> Select rpc, or /[search] to keep searching: 
>>> 2
--- slider popup ----
```
