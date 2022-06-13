# dev API – commands

In this page you'll find documentation regarding command registration, context generation & management, as well as some
other helper functions were solely designed to go hand in hand with commands.

Baseclasses for command registration are also included here, as well as cog-related classes.

***
## command registration

> ### `class` dev.utils.baseclass.GroupMixin
> A subclasses of [GroupMixin](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.GroupMixin) 
> that overrides command registering functionality. You would usually want to create an instance of this class and 
> start registering your commands from there.
> 
>> ### all_commands
>> A dictionary of all registered commands and their qualified names.
>>> #### Type
>>> Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), Union[[Command](), [Group]()]]

> ### `class` dev.utils.baseclass.Group
> A subclasses of [commands.Group](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Group) 
> which adds a few extra properties for commands.
> 
>> ### `property` global_use
>> Check whether this command is allowed to be invoked by any user.
>>> #### Type
>>> [bool](https://docs.python.org/3/library/functions.html#bool)
> 
>> ### `property` supports_virtual_vars
>> Check whether this command is compatible with the use of out-of-scope variables.
>>> #### Type
>>> [bool](https://docs.python.org/3/library/functions.html#bool)
> 
>> ### `property` supports_root_placeholder
>> Check whether this command is compatible with the `|root|` placeholder text.
>>> #### Type
>>> [bool](https://docs.python.org/3/library/functions.html#bool)

> ### `class` dev.utils.baseclass.Command
>> ### `property` global_use
>> Check whether this command is allowed to be invoked by any user.
>>> #### Type
>>> [bool](https://docs.python.org/3/library/functions.html#bool)
> 
>> ### `property` supports_virtual_vars
>> Check whether this command is compatible with the use of out-of-scope variables.
>>> #### Type
>>> [bool](https://docs.python.org/3/library/functions.html#bool)
> 
>> ### `property` supports_root_placeholder
>> Check whether this command is compatible with the `|root|` placeholder text.
>>> #### Type
>>> [bool](https://docs.python.org/3/library/functions.html#bool)
***
## cogs

> ### `class` dev.utils.baseclass.Root(bot)
> A cog base subclass that implements a global check and some default functionality that the dev extension should have.
> 
> Command uses and override callbacks are stored in here for quick access between different cogs.
>> ### Parameters
>> - bot([Bot](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Bot)) – The bot 
>> instance that gets passed to [commands.Bot.add_cog](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Bot.add_cog).
>
>> ### bot
>> The bot instance that was passed to [baseclass.Root]().
>>> #### Type
>>> [Bot](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Bot)
>
>> ### command_uses
>> A dictionary that keeps track of the amount of times a command has been used.
>>> #### Type
>>> Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), [int](https://docs.python.org/3/library/functions.html#int)]
>
>> ### root_command
>> The root command (`dev`) of the extension.
>>> #### Type
>>> Optional[Group]
>
>> ### CALLBACKS
>> Saved callbacks and source codes from command overrides or overwrites.
>>> #### Type
>>> Dict[[int](https://docs.python.org/3/library/functions.html#int), Tuple[[str](https://docs.python.org/3/library/stdtypes.html#str), [commands.Command.callback](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Command.callback), [str](https://docs.python.org/3/library/stdtypes.html#str)]]