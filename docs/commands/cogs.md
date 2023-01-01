# cogs

### `class` dev.utils.baseclass.Root(bot)

A cog subclass that implements a global check and some default functionality that the dev extension should have.

All other dev cogs will derive from this base class.

Command registrations are stored in here for quick access between different dev cogs.

Subclass
of [discord.ext.commands.Cog](https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Cog).

### Parameters

- bot([discord.ext.commands.Bot](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Bot)) –
The bot instance that gets passed
to [discord.ext.commands.Bot.add_cog](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Bot.add_cog).

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
> A check that is called every time a dev command is invoked. 
> This check is called internally, and shouldn't be called elsewhere.
>
> It first checks if the command is allowed for global use.  
> If that check fails, it checks if the author of the invoked command is specified in Settings.owners.  
> If the owner list is empty, it'll lastly check if the author owns the bot.
>
> If all checks
fail, [discord.ext.commands.NotOwner](https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.NotOwner)
is raised. This is done so that you can customize the message that is sent by the bot through an error handler.
> #### Parameters
> - ctx([discord.ext.commands.Context](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context)) –
> The invocation context in which the command was invoked.
> #### Returns
> [bool](https://docs.python.org/3/library/functions.html#bool) – Whether the user is allowed to use this command.
> #### Raises
> - [discord.ext.commands.NotOwner](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.NotOwner) –
    All checks failed. The user who invoked the command is not the owner of the bot.