# interactions

These are all functions that directly interact in some way with Discord, either by sending or handling messages, or
reacting.

***

### `class` dev.components.views.AuthoredView(author, *components)

A [discord.ui.View](https://discordpy.readthedocs.io/en/latest/interactions/api.html#discord.ui.View) wrapper that
automatically adds an owner-only interaction check.

#### Parameters

- author(Union[types.User, [int](https://docs.python.org/3/library/functions.html#int)]) – The only user that is allowed
  to interact with this view.
- components([discord.ui.Item](https://discordpy.readthedocs.io/en/latest/interactions/api.html#discord.ui.Item)) –
  Components that will be automatically added to the view.

#### Attributes

- author([int](https://docs.python.org/3/library/functions.html#int)) – The ID of the user that was passed to the
  constructor of this class.

***

### `class` dev.components.views.ModalSender(modal, /, author, **kwargs)

A view that automatically creates a button that sends a modal.

Subclass
of [AuthoredView](https://github.com/Lee-matod/dev/wiki/api#class-devcomponentsviewsauthoredviewauthor-components).

#### Parameters

- modal([discord.ui.Modal](https://discordpy.readthedocs.io/en/latest/interactions/api.html#discord.ui.Modal)) – The
  modal that will be sent on interaction.
- author(Union[types.User, [int](https://docs.python.org/3/library/functions.html#int)]) – The only user that is allowed
  to interact with this view.
- kwargs(Any) – Attributes that will be forwarded to the constructor
  of [discord.ui.Button](https://discordpy.readthedocs.io/en/latest/interactions/api.html#discord.ui.Button).

#### Attributes

- modal([discord.ui.Modal](https://discordpy.readthedocs.io/en/latest/interactions/api.html#discord.ui.Modal)) – The
  modal that was passed to the constructor of this class.

#### Methods

- sender([discord.ui.Button](https://discordpy.readthedocs.io/en/latest/interactions/api.html#discord.ui.Button)) – The
  button that handles sending the given modal.

***

### `class` *async with* dev.handlers.ExceptionHandler(message, /, on_error=None, *, save_traceback=False)

Handle any exceptions in an async context manager.
If any exceptions are raised during the process' lifetime, the bot will try to add reactions depending on the exception
value.

💢 – Syntax errors (EOFError, IndentationError).  
⏰ – Timeout errors (asyncio.TimeoutError, TimeoutError).  
❓ – Reference errors (ImportError, NameError).  
❗ – Runtime errors (IndexError, KeyError, TypeError, ValueError).  
⁉ – Arithmatic errors (ZeroDivisionError, FloatingPointError).  
‼ – Any other errors that don't fall under any of the previous categories.

#### Parameters

- message([discord.Message](https://discordpy.readthedocs.io/en/latest/api.html#discord.Message)) – The message that
  the reactions will be added to.
- on_error(Callable[[Optional[Type[[Exception](https://docs.python.org/3/library/exceptions.html#Exception)]], Optional[[Exception](https://docs.python.org/3/library/exceptions.html#Exception)], Optional[[TracebackType](https://docs.python.org/3/library/types.html#types.TracebackType)]], Any]) – An
  optional function that will receive any raised exceptions inside the context manager.  
  This function *can* be a coroutine.
- save_traceback([bool](https://docs.python.org/3/library/functions.html#bool)) – Whether to save a traceback if an
  exception is raised. Defaults to `False`.

> #### `classmethod` cleanup()
> Deletes any tracebacks that were saved if `send_traceback` was set to `True`.  
> This method should always get called once you have finished handling any tracebacks

***

### dev.handlers.replace_vars(string)

Replaces any instance of virtual variables with their respective values and returns the parsed string.

#### Parameters

- string([str](https://docs.python.org/3/library/stdtypes.html#str)) – The string that should get converted.
- scope([LocalGlobals](https://github.com/Lee-matod/dev/blob/main/docs/utils.md#class-devhandlersgloballocals__globalsnone-__localsnone-)) –
The scope that will be used when dealing with variables.

#### Returns

[str](https://docs.python.org/3/library/stdtypes.html#str) – The converted string with the values of the virtual
variables.

***

### `class` dev.pagination.Interface(paginator, author)

A paginator interface that implements basic pagination functionality.

Subclass of [discord.ui.View](https://discordpy.readthedocs.io/en/latest/api.html#discord.ui.View).

#### Parameters

- paginator([discord.ext.commands.Paginator](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Paginator)) –
A pagination instance from which to get the pages from.
- author(Union[types.User, [int](https://docs.python.org/3/library/functions.html#int)]) – The user that should be
  able to interact with this paginator. User ID or object can be passed.

#### Attributes

- paginator([discord.ext.commands.Paginator](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Paginator)) –
The pagination instance that was passed to the constructor.
- author([int](https://docs.python.org/3/library/functions.html#int)) – The ID of the user that is able to interact
  with this paginator. This is the result of the user ID or object that was passed to the constructor.

> #### `property` display_page
> [str](https://docs.python.org/3/library/stdtypes.html#str) – Returns the current page of the paginator.

> #### `property` current_page
> [int](https://docs.python.org/3/library/functions.html#int) – Returns the current page number of the paginator.

***

### `class` dev.pagination.Paginator

A [discord.ext.commands.Paginator](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Paginator)
wrapper.

This subclass deals with lines that are greater than the maximum page size by splitting them.

Subclass
of [discord.ext.commands.Paginator](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Paginator).

#### See Also

[discord.ext.commands.Paginator](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Paginator)
> ### add_line(lines="", *, empty=False)
> A wrapper to the
default [discord.ext.commands.Paginator.add_line](https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Paginator.add_line).
>
> Difference being that no TypeErrors are raised if the line exceeds the maximum page length.
> #### Parameters
> - line([str](https://docs.python.org/3/library/stdtypes.html#str)) –
    From [discord.ext.commands.Paginator.add_line](https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Paginator.add_line).
    The line that should be added to the paginator.
> - empty([bool](https://docs.python.org/3/library/functions.html#bool)) –
    From [discord.ext.commands.Paginator.add_line](https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Paginator.add_line).
    Whether an empty line should be added too.

***

### *await* dev.utils.functs.interaction_response(interaction, response_type, *args, **options)

Evaluates how to safely respond to a Discord interaction.

`content`, `embed`, `embeds`, `file`, `files`, `modal` and `view` can all be optionally passed as
positional arguments instead of keywords. Everything else that is available in
[discord.InteractionResponse.send_message](https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.InteractionResponse.send_message)
and [discord.InteractionResponse.edit_message](https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.InteractionResponse.edit_message)
remain as keyword arguments.

This replaces the token of the bot with '[token]' and converts any instances of a virtual variable's value back to
its respective key.

If the response type is set to InteractionResponseType.MODAL, then the first argument passed to `args`
should be the modal that should be sent.

#### See Also

[discord.InteractionResponse.send_message](https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.InteractionResponse.send_message), [discord.InteractionResponse.edit_message](https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.InteractionResponse.edit_message)

#### Parameters

- interaction([discord.Interaction](https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.Interaction)) –
The interaction that should be responded to.
- response_type(types.ResponseType) – The type of response that will be used to respond to the interaction.
  [discord.InteractionResponse.defer](https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.InteractionResponse.defer)
  isn't included.
- args(Union[
  Sequence[Any], [discord.Embed](https://discordpy.readthedocs.io/en/latest/api.html#discord.Embed), [discord.File](https://discordpy.readthedocs.io/en/latest/api.html#discord.File), [discord.ui.View](https://discordpy.readthedocs.io/en/latest/api.html#discord.ui.View), [discord.ui.Modal](https://discordpy.readthedocs.io/en/latest/api.html#discord.ui.Modal), [str](https://docs.python.org/3/library/stdtypes.html#str)]) –
  Arguments that will be passed
  to [discord.InteractionResponse.send_message](https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.InteractionResponse.send_message)
  or [discord.InteractionResponse.edit_message](https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.InteractionResponse.edit_message).
  Embeds and files can be inside a list, tuple or set to send multiple of these types.
- options – Keyword arguments that will be passed
  to [discord.InteractionResponse.send_message](https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.InteractionResponse.send_message)
  or [discord.InteractionResponse.edit_message](https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.InteractionResponse.edit_message).

#### Returns

Optional[[Paginator](https://github.com/Lee-matod/dev/wiki/api#class-devpaginationpaginatorpaginator_type--prefix-suffix-max_size2000-linesepn)] –
The paginator that is being used in the first message if `forced_paginator` was set to `False` and the function decided
to enable pagination for the response.

#### Raises

- [ValueError](https://docs.python.org/3/library/exceptions.html#ValueError) – `response_type` was set to `MODAL`, but
  the first
  argument of `args` was not the modal.
- [TypeError](https://docs.python.org/3/library/exceptions.html#TypeError) – An invalid response type was passed.
- [IndexError](https://docs.python.org/3/library/exceptions.html#IndexError) – `content` exceeded the 2000-character
  limit, and `view` did not permit pagination to work due to the amount of components it included.

***

### *await* dev.utils.functs.send(ctx, *args, **options)

Evaluates how to safely send a Discord message.

`content`, `embed`, `embeds`, `file`, `files`, `stickers` and `view` are all positional arguments. Everything else that
is
available
in [discord.ext.commands.Context.send](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context.send)
remain as keyword arguments.

This replaces the token of the bot with '[token]' and converts any instances of a virtual variable's value back to its
respective key.

#### See Also

[discord.ext.commands.Context.send](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context.send)

#### Parameters

- ctx([discord.ext.commands.Context](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context)) –
The invocation context in which the command was invoked.
- args(types.MessageContent) – Arguments that will be passed
  to [discord.ext.commands.Context.send](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context.send).
  Embeds and files can be inside a list, tuple or set to send multiple of these types.
- options – Keyword arguments that will be passed
  to [discord.ext.commands.Context.send](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context.send)
  as well as the option that specifies if the message is a codeblocks.

#### Returns

Tuple[[discord.Message](https://discordpy.readthedocs.io/en/latest/api.html#discord.Message),
Optional[[Paginator](https://github.com/Lee-matod/dev/wiki/api#class-devpaginationpaginatorpaginator_type--prefix-suffix-max_size2000-linesepn)]] –
The message that was sent and the paginator if `forced_pagination` was set to `False`.

#### Raises

- [IndexError](https://docs.python.org/3/library/exceptions.html#IndexError) – `content` exceeded the 2000-character
  limit, and `view` did not permit pagination to work due to the amount of components it included.