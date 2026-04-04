# Twinleaf RUI: Rpc User Interface
RUI is a multitool for controlling Twinleaf sensor RPCs, featuring fuzzy searching RPC names for easy command line use and a Qt slider GUI popup. It is based on the [twinleaf Python library](https://github.com/twinleaf/twinleaf-python).

## Installation
Install with PyPi using:

   pip install twinleaf-rui 


## RUI GUI
Usage:

    rui [flags] [search terms]

RUI's default behaviour is a slider interface that launches in a popup window. Search terms, if given, will use the search/select CLI pre-populate` the control panel (see below); otherwise, it will open a blank window with a search bar to add sliders with. The minimum and maximum values of sliders can be changed with the text boxes to the left and right of the slider, and sliders can be removed from the view with the trash can button.

### Flags
- `--restore` will reinstate RUI GUI's previous open sliders
- `--all` (`-a`) will select all matched RPCs instead of prompting for selection
- `--exact` (`-e`) will search for exact strings instead of fuzzy-searching
- `--multisearch` (`-m`) will search for RPCs that match any of the space-separated search terms
- `--root` (`-r`) and `--sensor` (`-s`) will specify the URL and route to look for a board at respectively

## RUI CLI
Usage:

    rui cli [flags] [search terms] [argument] # in any order

For terminal input, use RUI CLI, which asks for search terms to select one or more RPCs, and then prompts values to call them with. If search terms and/or a numeric argument are given, RUI CLI will use them without asking, otherwise it will prompt for them.
- Exit the RUI CLI with Ctrl+C (process interrupt signal) or by typing "quit" or "exit" in any prompt.
- Select multiple search results by inputting their indices separated by spaces, or select all results by inputting `*` instead of an index.
- All RUI GUI flags except `--restore` will have the same functionality in RUI CLI.
- `--peek` (`-p`) will just check the value(s) of selected RPC(s) without prompting to change

## Examples
```
$ rui cuotff #(sic)
[ 1. bar.data.cutoff(float)
[ 2. imu.data.cutoff(float)
[ 3. mcutemp.data.cutoff(float)
[ 4. sync.data.cutoff(float)
[ 5. vrail.data.cutoff(float)
[ Select rpc(s) by , or enter terms to narrow search:
>>> 2 3 4
# GUI opens
```
```
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
