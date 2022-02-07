Sublime Text package to integrate with the [gf GDB frontend](https://github.com/nakst/gf)

## Installation

1. Copy the contents of the repository to `/path/to/sublime/Packages/gf-integration`

2. Set the control pipe in gf settings. Either globally in `~/.config/gf2_config.ini` or locally in `.project.gf` in the directory gf will be launched in.

```
[pipe]
control=/path/to/my-pipe-name.dat
```

3. Set the control pipe in sublime package settings `/path/to/sublime/Packages/User/gf-integration.sublime-settings`

```json
{
    "pipe_path": "/path/to/sublime/Packages/gf-integration",
}
```

4. Configure the directory gf will be lanched in. 

Add it to the trusted folders in the global gf config `~/.config/gf2_config.ini`

```
[trusted_folders]
/path/to/dir
```

Set the sublime setting either globally in /path/to/sublime/Packages/User/gf-integration.sublime-settings`

```json
{
    "working_directory": "/path/to/dir",
}
```

or by creating a project and setting it inside `my-project.sublime-project` 

```json
{
    "settings": {
        "gf-integration.working_directory": "/path/to/dir",
    },
}
```

This is the directory `.project.gf` will be loaded from. This will also become the initial working directory of GDB and the program you are debugging. 

If you don't set the editor setting it will default to the directory of the active file opened in sublime at the time of gf launch (if any). If there is no such file it will be the directory of the sublime executable.

## Usage

All commands on the command pallette (ctrl+shift+p) start with `gf-integration`

Default breakpoint toggle key: F8
