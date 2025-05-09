# How to start all of dioptra servers in `tmux`

## What you need to know about `tmux`

1. `Tmux` is aan [easy to install](https://tmuxcheatsheet.com/how-to-install-tmux/) terminal multiplexer that allows coordinated terminal emulator to be launched in the same window
2. Traditional key-combinations of the terminal panels can be found in multiple online cheat-sheets: [here](https://tmuxcheatsheet.com), [GitHub](https://gist.github.com/MohamedAlaa/2961058), [reddit](https://www.reddit.com/r/linux4noobs/comments/wqlkuy/cheatsheet_with_tmux_shortcuts/), and [medium](https://medium.com/@Sle3pyHead/tmux-cheat-sheet-and-quick-guide-44038cbe2870)
3. The Dioptra's `dev-kb/tmux-start/start-all.sh` script leverages the existing shell scripts form `dev-kb/tmux-start`, `dev-kb/local-setup`, and `dev-kb/ml-flow` 
4. The `dev-kb/tmux-start/start-all.sh` script can launch full server set of the services needed to run Dioptra in multiple split-panes of `tmux` in apparently one terminal window


## How to use `dev-kb/tmux-start/start-all.sh`

0. Pre-requisite of using the `dev-kb/tmux-start/start-all.sh` script is installed `tmux` with version above `3.2`. You can learn [here](https://tmuxcheatsheet.com/how-to-install-tmux/) how to install `tmux` for your OS.
1. The `dev-kb/tmux-start/start-all.sh` script requires only one parameter to start servers: the name of the environment-config file. 
2. Config file structure is described in [local setup KB](../local-setup/README.md#config-file)
3. Launch the `start-all.sh` script directly from KB location:
```
<your-starting-path>/dev-kb/tmux-start/start-all.sh -e <path-to-env-file>/env-dev.cfg
```

## How to `stop` and `terminate` your running `tmux` server
### To terminate your current tmux  session-panels and quit `tmux` you can use either key combination or a command from one of the terminal panels of `tmux`:
### Terminate servers running:
- The script configures `tmux` to respond to mouse/touch-pad click selection of the panels and it mostly works 
- [Optional] If mouse acts out you can navigate between `tmux` panels you can use keyboard shortcuts of `Ctrl+B` + `←`|`↑`|`→`|`↓` 
- Once in tmux-pane with running server the `Ctrl+C` combination terminates the running server process. Once you see your regular terminal prompt indicates that the server process has terminated.
- Once all the panes have the server processes stopped - follow the Exit `tmux` steps.

### Exit tmux session:
- The easiest option is to type `tmux kill-session` command in any of the tmux panels
- [Optional] CLI command `tmux kill-session -t di-all`, which can be launched from any of the `tmux` terminal emulator panels. Note, that the CLI command doesn't ask any questions and just quits `tmux`.
- [Optional] Key combination `Ctrl + B` + `&` (mnemonics `Control-Board-End`). Then answer `Y` or `y` to the question `kill-window bash? (y/n)` asked in the bottom of the `tmux` multiplexer window

## Customizing your tmux
- Traditional Cut-Paste `Ctrl+C`-`Ctrl+V` in `tmux` environment usually require `xclip` or similar terminal interface installed and configured in your terminal environment. This KB-entry does not address these details.

___
## Observed Issues: 
___

### Occasionally (has been observed on Mac M2 with MacOS 15) in the described setup Redis server doesn't fully stop as a response to the stop command `Ctrl+C` in `tmux` panel as it should.

- In the case on MacOS 14+ the port (6379 for Redis) is occupied by zombie process you need to [list processes](https://dev.to/osalumense/how-to-kill-a-process-occupying-a-port-on-windows-macos-and-linux-gj8) using the occupied port number `:6379` 
```sh
sudo lsof -i -P | grep LISTEN | grep :6379
```

- The output of the command looks similar to the following:
```
redis-ser 12345           user    6u  IPv4 0xdcbae8c9a20e5b54      0t0    TCP *:6379 (LISTEN)
redis-ser 12345           user    7u  IPv6 0xdcbab5c0705ff728      0t0    TCP *:6379 (LISTEN)
```

- The process holding the port can be killed with the following command, where the `12345` is the process ID extracted in the output of the above command:
```sh
sudo kill -9 12345
``` 

