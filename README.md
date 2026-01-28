# findrpc.py: fuzzy-find rpcs
# TODO: UPDATE README
findrpc stores rpc lists in a hidden directory (`~/.rpc-lists`) and puts a neat python I/O bow with a simple fuzzy find algorithm over making rpc calls, saving time on the slow `tio-tool rpc-list` function or Trendline's gradually deteriorating menu, and memory on exact rpc names. It presently interfaces with the device through making shell calls to `tio-tool` (todo: interface directly with Rust library)

# Usage
`./findrpc.py [search terms] [arg]`
- Without any arguments, findrpc will prompt for both search terms and an argument.
- With only search terms, findrpc will prompt to select an rpc from the search results, see its current value, then ask for an argument. Enter nothing, `-`, `quit`, or `exit` to not change it.
- Select multiple search results by inputting their indices separated by spaces, or select all results by inputting `*` instead of an index.
    - If `*` is passed as an argument, findrpc will automatically select all results.
- Instead of an index, type /[search] to narrow the search further.
- If `-` is passed as an argument, findrpc will skip asking for an argument.
- If `+` is passed as an argument, findrpc will loop over calls to the select rpc until quit.
- If `@` is passed as an argument, findrpc will exact search instead of fuzzy search.
    - Put `@` in front of an argument to exact-search instead of fuzzy-search it. `.` in front of an argument will exact-search it including the `.`, so `./findrpc .lock` will get `...control.lockrange` but not `...capture.block`.
- If `regen` is passed as an argument, findrpc will re-fetch the rpc list and write to file (this takes a while).
- If only one result is found, findrpc will go directly to that rpc. So `./findrpc [exact search] [arg or -]` is the same as `tio-tool rpc [exact rpc name] [arg or N/A]` but with less demanding syntax.

# Examples
``` bash
$ ./findrpc.py septoint #(sic)
> 1. probe.therm.control.setpoint(f32)
> 2. pump.therm.control.setpoint(f32)
> 3. pump.therm.control.setpoint.min(f32)
> 4. pump.lock.control.setpoint(f32)
> 5. cell.therm.control.setpoint(f32)
>
> Select rpc:  ...  2
>
> Currently: 59.827354
> Enter argument: 60
> Reply: 60
```
``` bash
$ ./findrpc.py decim 1
> 1. field.data.decimation(u32)
> 2. vector.data.decimation(u32)
> 3. vectorcal.data.decimation(u32)
> 4. status.data.decimation(u32)
> 5. aux.data.decimation(u32)
> 6. therm.data.decimation(u32)
>
> Select rpc: *
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
