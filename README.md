# dev
A debugging, testing and editing cog for discord.py. This does not use slash commands (mainly because I think they're ugly), so message intents have to be enabled! (Or set the bot's prefix to its tag).

discord.py Github: https://github.com/Rapptz/discord.py

discord.py docs: https://discordpy.readthedocs.io/en/latest/index.html

This is still under development, so I'm terribly sorry if you experience any issues.

This README.md should also get edited in the near future with more stuff to read.
****
# settings

You can customize this extension however you'd like. To do this simply import `Settings` from `dev` and change the module and its setting accordingly. An example is shown below.
```python
from dev import Settings
Settings.OWNERS = [1234567890]
```
The full `settings` tree is shown below.
```python
FLAG_DELIMITER: str = ": "
INVOKE_ON_EDIT: Optional[bool] = True
OWNERS: Optional[Sequence[int]] = []
PATH_TO_FILE: Optional[str] = f"{os.getcwd()}"
ROOT_FOLDER: Optional[str] = ""
VIRTUAL_VARS: str = "|%(name)s|"
```
