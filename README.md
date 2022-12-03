# dev
dev is a debugging, testing and editing extension for discord.py.

discord.py github: https://github.com/Rapptz/discord.py  
discord.py docs: https://discordpy.readthedocs.io/en/latest/index.html

This cog is still under development, thus, certain aspects may be a bit unstable.
****
# installation

Python 3.8 or higher is required. To install the extension, simply execute the following command depending on what 
operating system you use.

**Windows**
```
py -3 -m pip install -U git+https://github.com/Lee-matod/dev
```
**MacOS/Linux**
```
python3 -m pip install -U git+https://github.com/Lee-matod/dev
```

# setup

```python
from discord.ext import commands

bot = commands.Bot(command_prefix=..., intents=...)

@bot.event
async def setup_hook() -> None:
    await bot.load_extension("dev")

bot.run("[token]")
```
If you're subclassing 
[discord.ext.commands.Bot](https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Bot):
```python
from discord.ext import commands

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(command_prefix=..., intents=...)
    
    async def setup_hook(self) -> None:
        await self.load_extension("dev")

bot = Bot(...)
bot.run("[token]")
```
****
# settings

There are a couple of ways to customize the cog. These are mostly done with the `Settings` class. An example is shown 
below as well as what they do.
```python
from dev import Settings
Settings.OWNERS = {1234567890}
Settings.INVOKE_ON_EDIT = True
Settings.VIRTUAL_VARS = "-%s-"
```
```python
ALLOW_GLOBAL_USES: bool = False
FLAG_DELIMITER: str = "="
INVOKE_ON_EDIT: bool = False
OWNERS: Set[int] = {}
PATH_TO_FILE: str = os.getcwd()
ROOT_FOLDER: str = ""
VIRTUAL_VARS: str = "|%s|"
RETENTION: bool = False
```
* **ALLOW_GLOBAL_USES:** Commands that have their `global_use` property set True are allowed to be invoked by any user. 
Defaults to `False`.
* **FLAG_DELIMITER:** The characters that determines when to separate a key from its value when parsing strings to 
dictionaries. Defaults to `=`.
* **INVOKE_ON_EDIT:** Whenever a message that invoked a command is edited to another command, the bot will try to invoke 
the new command. Defaults to `False`.
* **OWNERS:** A set of user IDs that override bot ownership IDs. If specified, users that are only found in the 
ownership ID list will not be able to use this extension.
* **PATH_TO_FILE:** A path directory that will be removed if found inside a message. This will typically be used in 
tracebacks. Defaults to the current working directory. This must be a valid path.
* **ROOT_FOLDER:** The path that will replace the `|root|` text placeholder. This must be a valid path.
* **VIRTUAL_VARS:** The format in which virtual variables are expected to be formatted. The actual place where the 
variable's name will be should be defined as `%s`. Defaults to `|%s|`.
