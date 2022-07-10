# dev
A debugging, testing and editing cog for discord.py. This does not use slash commands 
(mainly because I think they're ugly), so message intents have to be enabled! 
(or set the bot's prefix to its tag).

discord.py github: https://github.com/Rapptz/discord.py  
discord.py docs: https://discordpy.readthedocs.io/en/latest/index.html

This is still under development, so I'm terribly sorry if you experience any issues.  
This `README.md` should also get edited in the near future with more stuff to read.
****
# setup

Python 3.8 or higher is required. To install the extension, simply run the following command
on your console depending on what operating system you use.

**For Windows**
```
py -3 -m pip install -U git+https://github.com/Lee-matod/dev.git
```
**For Linux/MacOS**
```
python3 -m pip install -U git+https://github.com/Lee-matod/dev.git
```

In-code setup is quite simple. An example is shown below

```python
from discord.ext import commands

bot = commands.Bot(command_prefix=..., intents=...)

@bot.listen()  # or `@bot.event`, both work
async def setup_hook() -> None:
    await bot.load_extension("dev")
```
if you're subclassing commands.Bot
```python
from discord.ext import commands

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=..., intents=...)
    
    async def setup_hook(self) -> None:
        await self.load_extension("dev")
```
****
# settings

You can customize this extension however you'd like. To do this simply import `Settings` from `dev` and change 
its attributes accordingly. An example is shown below.
```python
from dev import Settings
Settings.OWNERS = [1234567890]
Settings.INVOKE_ON_EDIT = False
Settings.VIRTUAL_VARS = "-%(name)s-"
```
The full `settings` tree and what they do are shown below. Note that if the wrong type of value is passed, a 
`ValueError` exception will be raised.
```python
ALLOW_GLOBAL_USES: bool = False
FLAG_DELIMITER: str = "="
INVOKE_ON_EDIT: bool = True
OWNERS: Optional[Set[int]] = {}
PATH_TO_FILE: Optional[str] = os.getcwd()
ROOT_FOLDER: Optional[str] = ""
VIRTUAL_VARS: str = "|%(name)s|"
```
* **ALLOW_GLOBAL_USES:** Commands aren't considered very harmful or dangerous can be executed by every user. If this setting is enabled, then commands that are considered as 'not harmful' can be called by any user. This defaults to `False`.
* **FLAG_DELIMITER:** This setting is used to determine when to separate
keys and values when specifying any kwargs that should be passed in if the command supports these.
* **INVOKE_ON_EDIT:** If `True`, then a command will be reinvoked if it is edited.
* **OWNERS:** A list of user IDs that can override `bot.owner_id(s)` determining who can use the dev extension.
If none are specified, and the bot is logged in before the extension gets loaded, then it defaults to the ID of the owner of the bot.
* **PATH_TO_FILE:** If a traceback is sent, the path that is specified will be removed from it. This can be used to hide
personal names or unwanted information.
* **ROOT_FOLDER:** This is the path that is going to replace the `|root|` placeholder text.
* **VIRTUAL_VARS:** The format in which virtual variables should be specified.
