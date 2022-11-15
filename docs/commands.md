In this page you'll find documentation regarding command registration, context generation & management, as well as some
other helper functions that were solely designed to go hand-in-hand with commands.

Baseclasses for command registration are also included here, as well as cog-related classes.

This page does not showcase the actual features of this extension. Check out the [dev wiki](https://github.com/Lee-matod/dev/wiki/dev) for that.

## command registration

### `class` dev.utils.baseclass.root
A super class that allows the conversion of coroutine functions to temporary command classes that can later be used to 
register them as an actual [discord.ext.commands.Command](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Command).
 
Even though this class was made for internal uses, it cannot be instantiated nor subclassed. It should be used as-is.
> ### `staticmethod` @command(name=MISSING, **kwargs)
> A decorator that converts the given function to a temporary [Command](https://github.com/Lee-matod/dev/blob/main/docs/commands.md#class-devutilsbaseclasscommand) class.
> #### Parameters
> - name([str](https://docs.python.org/3/library/stdtypes.html#str)) – The name of the command that should be used. 
> If no name is provided, the function's name will be used.
> - kwargs – Key-word arguments that'll be forwarded to the [Command](https://github.com/Lee-matod/dev/blob/main/docs/commands.md#class-devutilsbaseclasscommand) class.

> ### `staticmethod` @group(name=MISSING, **kwargs)
> A decorator that converts the given function to a temporary [Group](https://github.com/Lee-matod/dev/blob/main/docs/commands.md#class-devutilsbaseclassgroup) class.
> #### Parameters
> - name([str](https://docs.python.org/3/library/stdtypes.html#str)) – The name of the command that should be used. 
> If no name is provided, the function's name will be used.
> - kwargs – Key-word arguments that'll be forwarded to the [Group](https://github.com/Lee-matod/dev/blob/main/docs/commands.md#class-devutilsbaseclassgroup) class.

***

### `class` dev.utils.baseclass.Group
A class that simulates [discord.ext.commands.Group](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Group).

This class is used to keep track of which functions be groups, and it shouldn't get called manually. 
Instead, consider using [root.group](https://github.com/Lee-matod/dev/blob/main/docs/commands.md#staticmethod-groupnamemissing-kwargs) to instantiate this class.
> ### to_instance(command_mapping, /)
> Converts this class to an instance of its respective simulation.
> #### Parameters
> - command_mapping(Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), types.Command]) – A mapping of 
> commands from which this group will get their corresponding parents from.
> #### Returns
> [discord.ext.commands.Group](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Group) – 
> The group class made using the given attributes of this temporary class.

***

### `class` dev.utils.baseclass.Command
A class that simulates [discord.ext.commands.Command](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Command).

This class is used to keep track of which functions should be commands, and it shouldn't get called manually. 
Instead, consider using [root.command](https://github.com/Lee-matod/dev/blob/main/docs/commands.md#staticmethod-commandnamemissing-kwargs) to instantiate this class.
> ### to_instance(command_mapping, /)
> Converts this class to an instance of its respective simulation.
> #### Parameters
> - command_mapping(Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), types.Command]) – A mapping of 
> commands from which this command will get their corresponding parents from.
> #### Returns
> [discord.ext.commands.Command](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Command) – 
> The command class made using the given attributes of this temporary class.

​

## cogs

### `class` dev.utils.baseclass.Root(bot)
A cog subclass that implements a global check and some default functionality that the dev extension should have.
Command registrations are stored in here for quick access between different dev cogs.
 
All other dev cogs will derive from this base class.
 
Subclass of [discord.ext.commands.Cog](https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Cog).
### Parameters
- bot([discord.ext.commands.Bot](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Bot)) – The bot 
instance that gets passed to [discord.ext.commands.Bot.add_cog](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Bot.add_cog).

> ### bot
> The bot instance that was passed to the constructor of this class.
> #### Type
> [discord.ext.commands.Bot](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Bot)

> ### commands
> A dictionary that stores all dev commands.
> #### Type
> Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), types.Command]

> ### registrations
> A dictionary that stores all modifications made in the `dev override`/`dev overwrite` commands.
> #### Type
> Dict[[int](https://docs.python.org/3/library/functions.html#int), Union[CommandRegistration, SettingRegistration]]

> ### *await* cog_check(ctx)
> A check that is called every time a dev command is invoked. This check is called internally, and shouldn't be called 
> elsewhere.
>
> It first checks if the command is allowed for global use. 
> If that check fails, it checks if the author of the invoked command is specified in Settings.OWNERS. 
> If the owner list is empty, it'll lastly check if the author owns the bot.
>
> If all checks fail, [discord.ext.commands.NotOwner](https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.NotOwner)
> is raised. This is done so that you can customize the message that is sent by the bot through an error handler.
> #### Parameters
> - ctx([discord.ext.commands.Context](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context)) – 
> The invocation context in which the command was invoked.
> #### Returns
> [bool](https://docs.python.org/3/library/functions.html#bool) – Whether the user is allowed to use this command.
> #### Raises
> - [discord.ext.commands.NotOwner](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.NotOwner) – 
> All checks failed. The user who invoked the command is not the owner of the bot.