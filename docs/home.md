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
[Settings.flag_delimiter](https://github.com/Lee-matod/dev#settings) character.

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

### Can I add my own commands?

Yes! This extension is fully extendable. To create your own cogs, you must
use [Plugin](https://github.com/Lee-matod/dev/blob/main/docs/commands/cogs.md#class-devrootpluginbot) instead
of [discord.ext.commands.Cog](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Cog),
and use [command](https://github.com/Lee-matod/dev/blob/main/docs/commands/registration.md#devrootcommandnamemissing-kwargs) to
register your commands. Besides that, it is as simple as creating any other cog.  
**Note:** When creating subcommands, do not do `@parent_command.command()` as this decorator does not exist.
Instead, use `@root.command(...)` and set the `parent` key word argument to the fully qualified name of
the parent command.

```python
# ~/cog.py
from dev import root
from discord.ext import commands


class MyDevCog(root.Plugin):
    # The 'parent' keyword argument is optional. For the purpose of this
    # example though, we are going to be adding these custom commands as
    # subcommands of 'dev'.

    # 'parent' is the only public additional argument that can be
    # added to the decorator. Everything else is passed directly to the
    # command constructor.
    @root.group(name="custom_group", parent="dev", invoke_without_command=True)
    async def my_custom_group(self, ctx: commands.Context) -> None:
        await ctx.send("This is a custom group!")

    # Note that we are using the qualified name of the parent:
    @root.command(name="custom_subcommand", parent="dev custom_group")
    async def my_custom_subcommand(self, ctx: commands.Context) -> None:
        await ctx.send("This is a custom subcommand!")

    @root.command(name="custom_command", parent="dev")
    async def my_custom_command(self, ctx: commands.Context) -> None:
        await ctx.send("This is a custom command!")


# This part is mandatory just like with any other extension.
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MyDevCog(bot))
```

Once you have created your custom cog, you load it like you would with any other extension.

```python
# ~/__main__.py
import discord
from discord.ext import commands

intents = discord.Intents.default()
# Message content intent is required to be able to use message/prefix commands. 
# Alternatively, set the bot's prefix to its mention.
intents.message_content = True
bot = commands.Bot(command_prefix="?", intents=intents)


@bot.event
async def setup_hook():
    # Sometimes the order of this matters.
    # If your custom cog interacts in any way with the extension,
    # you should load dev first, and then your cog.
    await bot.load_extension("dev")
    await bot.load_extension("cog")


bot.run("[token]")
```

Congratulations! You have your very own custom command. You can now access these commands by
running `?dev custom_command`, `?dev custom_group`, or `?dev custom_group custom_subcommand`.  
This also means that all 3 custom commands are bound to the owner-only check.

It is worth mentioning that using the [discord.ext.commands](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html)
framework is also supported and commands registered this way will work as if the cog where normal.

### Can I override a root command?

This is also possible! The steps are pretty similar on adding custom commands too.
To override a command, you just have to copy the qualified name and use it as your command's name.

```python
#  ~/override.py
from dev import root
from discord.ext import commands


class MyDevCog(root.Plugin):
    # Be careful what type of command you use when overriding commands.
    # If you use `root.command` with an expected group command, you will
    # get an error!

    # We are going to override the root command here.
    # Remember that if we don't set `invoke_without_command`,
    # this command will be invoked when using its subcommands.
    @root.group(name="dev", invoke_without_command=True)
    async def my_custom_group(self, ctx: commands.Context) -> None:
        await ctx.send("No more system information for you!")

    # And let's override the 'dev override' command too.
    # You can of course change command attributes, signature,
    # and functionality. But for the sake of simplicity, I will just
    # send a message and make the command essentially useless.
    @root.command(name="override", parent="dev")
    async def my_custom_subcommand(self, ctx: commands.Context) -> None:
        await ctx.send("Well this is ironic...")

# This part is mandatory just like with any other extension.
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MyDevCog(bot))
```

Maybe you still need the default functionality of a command, but just want to add a bit of logging to it. You don't
have to copy and paste the implementation of the whole command. Instead, subclass the Root cog of the command, and
override the method of the command.  
Root cogs are not documented and aren't in `dev.__all__`, but they can be found under the `plugins` package.

```python
#  ~/logged_python.py
import logging

from dev import root, plugins
from discord.ext import commands

_log = logging.getLogger(__name__)


class MyRootPython(plugins.RootPython):
    # Since we are technically just overriding a method,
    # the name of the method should be exactly the same.
    
    @root.command(name="python", parent="dev", aliases=["py"])
    async def root_python(self, ctx: commands.Context, *, code: str) -> None:
        _log.info("Command '%s' called by %s", ctx.command.qualified_name, ctx.author)
        await super().root_python(ctx, code=code)
        _log.info("Command '%s' finished executing", ctx.command.qualified_name)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MyRootPython(bot))
```

Now that we have overridden a few root commands and added some extra implementation, we can load the extension in our
main file.

```python
# ~/__main__.py
import discord
from discord.ext import commands

intents = discord.Intents.default()
# Message content intent is required to be able to use message/prefix commands. 
# Alternatively, set the bot's prefix to its mention.
intents.message_content = True
bot = commands.Bot(command_prefix="?", intents=intents)


@bot.event
async def setup_hook():
    # Both of these custom extensions interact with the dev cog,
    # so (as mentioned above), they must be after the extension.
    await bot.load_extension("dev")
    await bot.load_extension("override")
    await bot.load_extension("logged_python")


bot.run("[token]")
```

If you happen to unload an extension, all of the commands that override any other command will be removed and replaced
with a previous version of it until it reaches the root command.  
As an example, if you override the command `dev` in a cog called `DevOverride`, when you add the cog, the root `dev`
command will be overridden with the new implementation of `DevOverride`. However, when you remove the cog, the command
of `DevOverride` will be removed and the original `dev` command will take its place.

With that little note out of the way, congratulations! You have your very own `dev`, `dev python|py` and
`dev override` commands!