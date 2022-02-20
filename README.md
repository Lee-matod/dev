# dev
A debugging, testing and editing cog for enhanced-dpy.

enhanced-dpy Github: https://github.com/iDevision/enhanced-discord.py

enhanced-dpy docs: https://enhanced-dpy.readthedocs.io/en/latest/index.html

This is still under development, so I'm terribly sorry if you experience any issues.

This README.md should also get edited in the near future with more stuff to read.
****
# settings
```
"folder":
    "path_to_file": None,   # type: str
    "root_folder": None  # type: str
    
"kwargs":
    "separator": "=",  # type: str
    "format": "%(key)s%(sep)s%(word)s"  # type: str

"source":
    "filename": None,  # type: str
    "use_file": False,  # type: bool
    "not_dev_cmd": "./",  # type: str
    "show_path": False  # type: bool

"file": {
    "use_file": False,  # type: bool
    "/": "/",  # type: str
    "show_path": True  # type: bool

"owners": None  # type: Union[list, tuple, set]
```

**global**

"path_to_file": The path specified will be used instead of the actual directory to a file when an exception occurs, and it is sent as a message.

"root_folder": The path specified will be the one that replaces the `/root/` placeholder text.

"separator": Character(s) that separates the keyword from the argument.

"format": Format that is used for the kwargs.

**?dev --source|-src**

"filename": This replaces the filename with a string of choice.

"use_file": Whether the bot should send a file or a paginator.

"not_dev_cmd": Whether the command should be taken as a `?dev` command or as a foreign one.

"show_path": Whether the path for the file should be sent or not.

**?dev --file**

"use_file": Whether the bot should send a file or a paginator.

"/": "/": If the directory starts with `settings["file"]["/"]`, the directory specified should start at `/` instead of the current working directory.

"show_path":  Whether the path for the file should be sent or not.