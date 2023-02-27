Welcome to the dev wiki!  
In this page, you'll find some example use cases of every feature and command, a Frequently Asked Questions tab, and
what each other page is about.

## documentation

[api wiki](https://github.com/Lee-matod/dev/wiki/api) – Classes and functions that you can use anywhere, regardless if
you use the extension as a cog.  
[commands wiki](https://github.com/Lee-matod/dev/wiki/commands) – Public classes that are used for registering the
various commands included in this extension.  
[utils wiki](https://github.com/Lee-matod/dev/wiki/utils) – Other helper classes and functions that didn't fall under
any other category.

## FAQ

### How can I invoke an application command?

All the commands included in the RootInvoke cog (currently `timeit`, `repeat`, `debug`, and `execute`) accept
application commands in their `command_name` parameters.  
To specify a slash command instead of a message command, prefix the command's name with a slash (`/`) followed by the
fully qualified name of the command (just like with normal prefix commands).

When specifying arguments, you must provide them in a new line as name-value pairs, where each pair is separated by the
[Settings.flag_delimiter](https://github.com/Lee-matod/dev#settings) character sequence.

As an example, I will create an application command that looks a bit like this:

```python
import discord
from discord import app_commands

#  In this example, we will be using the default
#  flag delimiter which is '='.
@app_commands.command()
async def example(
        interaction: discord.Interaction,
        name: str,
        age: int,
        can_drive: bool = False
):
    fmt = "can drive" if can_drive else "cannot drive"
    await interaction.response.send_message(f"Greetings, {name}! You are {age} years old and {fmt}.")
```

After syncing this command with Discord, I will invoke it using the `dev exec` command.

![Lee_ executing ?dev exec /example in discord](https://user-images.githubusercontent.com/89663192/212227121-8b8e28a8-1613-41d1-b6ae-6d09be68edf3.png)

Removed timestamps to make image clearer

The first thing that you might notice when viewing this image, is that the order of the parameters does not matter, and
this is thanks to the way in which each parameter name and value are parsed (see notes below for a more in-depth
explanation).  
An additional thing to note is that, when specifying parameter names, you must use its
[display_name](https://discordpy.readthedocs.io/en/latest/interactions/api.html#discord.app_commands.Parameter.display_name)
and not its actual function name.

**DISCLAIMER:** Locale is *not* currently supported in this environment. This is also an experimental feature, so be
sure to report any bugs in the [issue tracker](https://github.com/Lee-matod/dev/issues).

> #### Note
> At the time of writing this, an application command's interface does not support new lines without doing some
> wacky stuff. This is why I opted for each argument to be in a separate line rather than parsing a whole single line of
> arguments.
>
> Additionally, (as noted by Gorialis in
> [this issue comment](https://github.com/Gorialis/jishaku/issues/185#issuecomment-1329579269)) an application command's
> parameter can perfectly accept `""""` as an argument, which makes parsing a lot more complicated than it has to be.

### Can I add my own commands?

Yes! This extension is fully extendable. To create your own cogs, you must
use [Container](https://github.com/Lee-matod/dev/wiki/commands#class-devutilsbaseclassrootbot) instead
of [discord.ext.commands.Cog](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Cog)
as the cog's parent class, and use [commands](https://github.com/Lee-matod/dev/wiki/commands#class-devutilsbaseclassroot) to
register your commands. Apart from that, it is as simple as creating any other extension.  
**Note:** When creating subcommands, do not do `@parent_command.command()` (like with normal commands) as this decorator
does not exist. Instead, use `@root.command(...)` and set the `parent` key word argument to the fully qualified name of
the parent command.

```python
#  cog.py
from dev import root
from discord.ext import commands


class MyDevCog(root.Container):
    #  The 'parent' keyword argument is optional. If you don't set it, 
    #  it will mean that the cog loader should treat the command as if 
    #  it is part of the 'Dev' cog, but it is not a subcommand of 'dev'.
    #  For the purpose of this example though, we are going to be adding 
    #  these custom commands as subcommands of 'dev'.

    @root.group(name="custom_group", parent="dev", invoke_without_command=True)
    async def my_custom_group(self, ctx: commands.Context) -> None:
        await ctx.send("This is a custom group!")

    @root.command(name="custom_subcommand", parent="dev custom_group")
    async def my_custom_subcommand(self, ctx: commands.Context) -> None:
        await ctx.send("This is a custom subcommand!")

    @root.command(name="custom_command", parent="dev")
    async def my_custom_command(self, ctx: commands.Context) -> None:
        await ctx.send("This is a custom command!")


#  This part is mandatory just like with any other cog.
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MyDevCog(bot))
```

Once you have created your custom cog, you have to load it like you would with any other extension.

```python
#  __main__.py
import discord
from discord.ext import commands

intents = discord.Intents.default()
#  Message content intent is required to be able to use message/prefix commands. 
#  Alternatively, set the bot's prefix to its mention.
intents.message_content = True
bot = commands.Bot(command_prefix="?", intents=intents)


@bot.event
async def setup_hook():
    #  When adding **other custom commands**, the order in which you 
    #  load the extension does not matter.
    await bot.load_extension("cog")
    await bot.load_extension("dev")


bot.run("[token]")
```

Congratulations! You have your very own custom command. You can now access these commands by
running `?dev custom_command`, `?dev custom_group`, or `?dev custom_group custom_subcommand`.  
This also means that all 3 custom commands are bound to the owner-only check.

This is also compatible with
the [discord.ext.commands](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html) framework.

### Can I override a root command?

Sure can do! The steps are pretty similar on adding custom commands too. You just have to make sure that you load your
custom cog with the override *after* you load the dev extension, otherwise your commands won't get overridden.  
To override a command, you just have to copy the qualified name and use it as your command's name.

```python
#  override.py
from dev import root
from discord.ext import commands


class MyDevCog(root.Container):
    #  Be careful what type of command you use when overriding commands.
    #  If you use `root.command` with an expected group command, you will
    #  get an error!

    #  We are going to override the root command here.
    #  Remember that if we don't set `invoke_without_command`,
    #  this command will be invoked when using its subcommands.
    @root.group(name="dev", invoke_without_command=True)
    async def my_custom_group(self, ctx: commands.Context) -> None:
        await ctx.send("No more system information for you!")

    #  And let's override the 'dev override command' command.
    @root.command(name="command", parent="dev override")
    async def my_custom_subcommand(self, ctx: commands.Context) -> None:
        await ctx.send("Well this is ironic... can't override commands anymore!")

#  This part is mandatory just like with any other cog.
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MyDevCog(bot))
```

Maybe you still need the default functionality of a command, but just want to add a bit of logging. Wait! don't copy and
paste the implementation of the command. Instead, subclass the Root cog of the command, and override the method of the
command.  
Root cogs are not documented, so if for whatever reason you want to do this, you will have to look for the name of the
class yourself. Root commands aren't registered in `dev.__all__` either, so you have to get them through the module.  
Each module is inside a package that includes the cogs in their respective `__all__` (except for `dev.__main__`), so you
can use either the full namespace, or just the package namespace.

```python
#  new_python.py
import logging

from dev import root
from dev.experimental import RootPython
#  from dev.experimental.python import RootPython  # Can also use the full namespace
from discord.ext import commands

_log = logging.getLogger(__name__)


class MyRootPython(RootPython):
    #  Since we are technically just overriding a method,
    #  the name of the method should be exactly the same.
    
    @root.command(name="python", parent="dev", aliases=["py"])
    async def root_python(self, ctx: commands.Context, *, code: str) -> None:
        _log.info("Command 'dev python' called by %s", ctx.author)
        await super().root_python(ctx, code=code)
        _log.info("Command 'dev python' finished executing")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MyRootPython(bot))
```

Now that we have overridden a few root commands and added some extra implementation, we can load the extension in our
main file.

```python
#  __main__.py
import discord
from discord.ext import commands

intents = discord.Intents.default()
#  Message content intent is required to be able to use message/prefix commands. 
#  Alternatively, set the bot's prefix to its mention.
intents.message_content = True
bot = commands.Bot(command_prefix="?", intents=intents)


@bot.event
async def setup_hook():
    #  REMEMBER! When overriding commands, you must **always**
    #  load the custom cog **after** you load the dev extension.
    #  This is due to how subclassing and registering works.
    await bot.load_extension("dev")
    await bot.load_extension("override")
    await bot.load_extension("new_python")


bot.run("[token]")
```

Congratulations, you have your very own `dev`, `dev python|py` and `dev override command` commands!