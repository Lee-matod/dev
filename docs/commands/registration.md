# command registration

## @dev.root.command(name=MISSING, **kwargs)
A decorator that converts the given function to a
temporary [Command](https://github.com/Lee-matod/dev/blob/main/docs/commands/registration.md#class-devutilsbaseclasscommand) class.
#### Parameters
- name([str](https://docs.python.org/3/library/stdtypes.html#str)) – The name of the command that should be used. If
  no name is provided, the function's name will be used.
- kwargs – Keyword arguments that will be forwarded to
  the [Command](https://github.com/Lee-matod/dev/blob/main/docs/commands/registration.md#class-devutilsbaseclasscommand) class.

## @dev.root.group(name=MISSING, **kwargs)
A decorator that converts the given function to a
temporary [Group](https://github.com/Lee-matod/dev/blob/main/docs/commands/registration.md#class-devutilsbaseclassgroup) class.
#### Parameters
- name([str](https://docs.python.org/3/library/stdtypes.html#str)) – The name of the command that should be used. If
  no name is provided, the function's name will be used.
- kwargs – Key-word arguments that'll be forwarded to
  the [Group](https://github.com/Lee-matod/dev/blob/main/docs/commands/registration.md#class-devutilsbaseclassgroup) class.

***

### `class` dev.utils.baseclass.Group

A class that
simulates [discord.ext.commands.Group](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Group).

This class is used to keep track of which functions be groups, and it shouldn't get called manually.
Instead, consider
using [group](https://github.com/Lee-matod/dev/blob/main/docs/commands/registration.md#devrootgroupnamemissing-kwargs) to
instantiate this class.
> ### to_instance(mixin, command_mapping, /)
> Converts this class to an instance of its respective simulation.
> #### Parameters
> - mixin([GroupMixin](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.GroupMixin)) –
> Where the command mapping should be obtained, and where to remove redifined commands from.
> - command_mapping(Optional[Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), types.Command]]) – A mapping of 
>   commands from which this group will get their corresponding parents from.
> #### Returns
> [discord.ext.commands.Group](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Group) –
> The group class made using the given attributes of this temporary class.

***

### `class` dev.utils.baseclass.Command

A class that
simulates [discord.ext.commands.Command](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Command).

This class is used to keep track of which functions should be commands, and it shouldn't get called manually.
Instead, consider
using [command](https://github.com/Lee-matod/dev/blob/main/docs/commands/registration.md#devrootcommandnamemissing-kwargs)
to instantiate this class.
> ### to_instance(mixin, command_mapping, /)
> Converts this class to an instance of its respective simulation.
> #### Parameters
> - mixin([GroupMixin](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.GroupMixin)) –
> Where the command mapping should be obtained, and where to remove redifined commands from.
> - command_mapping(Optional[Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), types.Command]]) – A mapping of
> commands from which this command will get their corresponding parents from.
> #### Returns
> [discord.ext.commands.Command](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Command) –
> The command class made using the given attributes of this temporary class.
