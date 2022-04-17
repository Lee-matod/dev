# dev
A debugging, testing and editing cog for discord.py. This does not use slash commands (mainly because I think they're ugly), so message intents have to be enabled!

discord.py Github: https://github.com/Rapptz/discord.py

discord.py docs: https://discordpy.readthedocs.io/en/latest/index.html

This is still under development, so I'm terribly sorry if you experience any issues.

This README.md should also get edited in the near future with more stuff to read.
****
# settings

You can customize this extension however you'd like. To do this simply import `settings` from `dev` and change the module and its setting accordingly. An example is shown below.
```python
from dev import settings
settings["owners"] = [1234567890]
```
The full `settings` tree is shown below.
```
"path_to_file": f"{os.getcwd()}",   # type: str
"root_folder": "",  # type: str
"virtual_vars_format": "|%(name)s|",  # type: str
"owners": []  # type: List[int], Tuple[int], Set[int]
```
**path_to_file**
If specified, any instances of this string in a traceback will be removed before sending. Defaults to your current working directory.

**root_folder**
If specified, typing out `|root|` will convert it to the directory specified.

**virtual_vars_format**
The format in which a virtual variable should be defined. `%(name)s` represents the name of the virtual variable. Defaults to `|VIRTUAL_VAR_NAME|`.

**owners**
If specified, this list of user IDs will be used to define users that are able to execute `dev`.
