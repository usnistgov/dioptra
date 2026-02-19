# How to start all of the dioptra services using `tmux`

## What you need to know about `tmux`

1. `Tmux` is an [easy to install](https://tmuxcheatsheet.com/how-to-install-tmux/) terminal multiplexer that allows coordinated terminal emulators to be launched in the same window
2. Traditional key-combinations of the terminal panels can be found in multiple online cheat-sheets: [here](https://tmuxcheatsheet.com), [GitHub](https://gist.github.com/MohamedAlaa/2961058), [reddit](https://www.reddit.com/r/linux4noobs/comments/wqlkuy/cheatsheet_with_tmux_shortcuts/), and [medium](https://medium.com/@Sle3pyHead/tmux-cheat-sheet-and-quick-guide-44038cbe2870)
3. The Dioptra's `dev-kb/tmux-start/start-all.sh` script also leverages shell scripts from `dev-kb/local-setup`, and `dev-kb/ml-flow`.
4. The `dev-kb/tmux-start/start-all.sh` script can launch the full set of services needed to run Dioptra in multiple split-panes of `tmux` in a single terminal window.


## How to use `dev-kb/tmux-start/start-all.sh`

0. Pre-requisite for using the `dev-kb/tmux-start/start-all.sh` script is to installed `tmux` with a version greater than `3.2`. Look [here](https://tmuxcheatsheet.com/how-to-install-tmux/) for instructions on how to install `tmux` for your OS.
1. The `dev-kb/tmux-start/start-all.sh` script requires only one parameter to start the services: the name of the environment-config file. 
2. Config file structure is described in [local setup](../local-setup/README.md#config-file)
3. To launch the `start-all.sh` script directly from this article's location:
```
<your-starting-path>/dev-kb/tmux-start/start-all.sh -e <path-to-env-file>/env-dev.cfg
```
For example if you are in the Dioptra code-directory and your environment config is in a parent directory, the command may look like the following:
```
./dev-kb/tmux-start/start-all.sh -e ../my-dev-env.cfg
```

## How to `stop` and `terminate` your running `tmux` server
### To terminate your current tmux  session-panels and quit `tmux` you can use either key-combination or a terminal command from any of the `tmux` terminal panels:
### Terminate servers running:
- The script configures `tmux` to respond to mouse/touch-pad click selection of the panels, and it should generally work. (Although some issues have been noticed.) 
- [Optional] You can also navigate between `tmux` panels using keyboard shortcuts. The shortcuts of `Ctrl+B` + `←`|`↑`|`→`|`↓` (arrow buttons) allow you to select active panels.
- Once in a tmux-pane with a running service the `Ctrl+C` combination terminates the running service process. Once you see your regular terminal prompt, this indicates that the service process has terminated.
- Once all the panes have the service processes stopped - follow the Exit `tmux` steps.

### Exit tmux session:
- The easiest option is to type `tmux kill-server` command in any of the tmux panels.
- [Optional] CLI command `tmux kill-session -t di-all`, which can be launched from any of the `tmux` terminal emulator panels. Note, that the CLI command doesn't offer any prompts and just quits `tmux`.
- [Optional] Key combination `Ctrl + B` + `&` (mnemonics `Control-Board-End`). Then answer `Y` or `y` to the question `kill-window bash? (y/n)` asked in the bottom of the `tmux` multiplexer window

## Customizing your tmux
- Traditional Cut-Paste `Ctrl+C`-`Ctrl+V` in `tmux` environment usually requires `xclip` or similar terminal interface installed and configured in your terminal environment. This KB-entry does not address these details.

___
## Observed Issues: 
___

### Occasionally (has been observed on Mac M2 with MacOS 15) in the described setup Redis and/or MLFlow servers don't fully stop on issuance of the stop command `Ctrl+C` in `tmux` panel as they should.

- In the case on MacOS 14+ the ports 6379 (for Redis) and or 35000 (for MLFLow) are occupied by "zombie- process" you need to [list processes](https://dev.to/osalumense/how-to-kill-a-process-occupying-a-port-on-windows-macos-and-linux-gj8) using the occupied port numbers `:6379` and/or `:35000`
```sh
sudo lsof -i -P | grep LISTEN | grep :6379
```
and /or
```sh
sudo lsof -i -P | grep LISTEN | grep :35000
```
- The output of the command looks similar to the following:
```
redis-ser 12345           user    6u  IPv4 0xdcbae8c9a20e5b54      0t0    TCP *:6379 (LISTEN)
redis-ser 12345           user    7u  IPv6 0xdcbab5c0705ff728      0t0    TCP *:6379 (LISTEN)
```

- The process holding the port can be killed with the following command, where the `12345` (the second column value) is the process ID extracted in the output of the above command:
```sh
sudo kill -9 12345
``` 

