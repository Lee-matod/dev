# command registration

### `class` dev.utils.baseclass.root

A super class that allows the conversion of coroutine functions to temporary command classes that can later be used to
register them as an
actual [discord.ext.commands.Command](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Command).

Even though this class was made for internal uses, it cannot be instantiated nor subclassed. It should be used as-is.
> ### `staticmethod` @command(name=MISSING, **kwargs)
> A decorator that converts the given function to a
temporary [Command](https://github.com/Lee-matod/dev/blob/main/docs/commands.md#class-devutilsbaseclasscommand) class.
> #### Parameters
> - name([str](https://docs.python.org/3/library/stdtypes.html#str)) – The name of the command that should be used. If
    no name is provided, the function's name will be used.
> - kwargs – Key-word arguments that'll be forwarded to
    the [Command](https://github.com/Lee-matod/dev/blob/main/docs/commands.md#class-devutilsbaseclasscommand) class.

> ### `staticmethod` @group(name=MISSING, **kwargs)
> A decorator that converts the given function to a
temporary [Group](https://github.com/Lee-matod/dev/blob/main/docs/commands.md#class-devutilsbaseclassgroup) class.
> #### Parameters
> - name([str](https://docs.python.org/3/library/stdtypes.html#str)) – The name of the command that should be used. If
    no name is provided, the function's name will be used.
> - kwargs – Key-word arguments that'll be forwarded to
    the [Group](https://github.com/Lee-matod/dev/blob/main/docs/commands.md#class-devutilsbaseclassgroup) class.

***

### `class` dev.utils.baseclass.Group

A class that
simulates [discord.ext.commands.Group](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Group).

This class is used to keep track of which functions be groups, and it shouldn't get called manually.
Instead, consider
using [root.group](https://github.com/Lee-matod/dev/blob/main/docs/commands.md#staticmethod-groupnamemissing-kwargs) to
instantiate this class.
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

A class that
simulates [discord.ext.commands.Command](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Command).

This class is used to keep track of which functions should be commands, and it shouldn't get called manually.
Instead, consider
using [root.command](https://github.com/Lee-matod/dev/blob/main/docs/commands.md#staticmethod-commandnamemissing-kwargs)
to instantiate this class.
> ### to_instance(command_mapping, /)
> Converts this class to an instance of its respective simulation.
> #### Parameters
> - command_mapping(Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), types.Command]) – A mapping of
    > commands from which this command will get their corresponding parents from.
> #### Returns
> [discord.ext.commands.Command](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Command) –
> The command class made using the given attributes of this temporary class.