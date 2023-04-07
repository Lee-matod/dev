# dev

dev is a debugging, testing and editing extension for discord.py.

discord.py github: https://github.com/Rapptz/discord.py  
discord.py docs: https://discordpy.readthedocs.io/en/latest/index.html

You can find the official documentation for this extension [here](https://github.com/Lee-matod/dev/wiki).
****

# installation

Python 3.8 or higher is required. To install the extension, simply execute the following command depending on what
operating system you use.

**Windows**

```shell
py -3 -m pip install -U git+https://github.com/Lee-matod/dev
```

**MacOS/Linux**

```shell
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
GLOBAL_USE: bool = False
FLAG_DELIMITER: str = "="
INVOKE_ON_EDIT: bool = False
LOCALE: str = "en-US"
OWNERS: set[int] = {}
PATH_TO_FILE: str = os.getcwd()
RETAIN: bool = False
ROOT_FOLDER: str = ""
VIRTUAL_VARS: str = "|%s|"
```

* **GLOBAL_USE:** Commands that have their `global_use` property set to True are allowed to be invoked by any user.
  Defaults to `False`.
* **FLAG_DELIMITER:** The characters that determines when to separate a key from its value when parsing strings to
  dictionaries. Defaults to `=`.
* **INVOKE_ON_EDIT:** Whenever a message that invoked a command is edited to another command, the bot will try to invoke
  the new command. Defaults to `False`.
* **LOCALE:** The default guild and user locale to use whenever emulating a Discord object. Defaults to `en-US`.
* **OWNERS:** A set of user IDs that override bot ownership IDs. If specified, users that are only found in the
  ownership ID list will be able to use this extension.
* **PATH_TO_FILE:** A directory that will be removed if found inside a message. This will typically be used in
  tracebacks. Defaults to the current working directory. This must be a valid path.
* **RETAIN:** Whether REPL sessions should retain their scope. This is only used in the `dev python` command. Defaults
  to `False`.
* **ROOT_FOLDER:** The path that will replace the `|root|` text placeholder. This must be a valid path.
* **VIRTUAL_VARS:** The format in which environment variables are expected to be defined. The actual place where the
  variable's name will be should be `%s`. Defaults to `|%s|`.
