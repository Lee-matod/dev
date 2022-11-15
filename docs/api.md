There are a lot of functions and classes that are used within this extension to facilitate the execution of certain 
tasks. This page focuses on documenting the numerous features that are included in the dev extension, so you can 
implement them in your own code if you'd like to.

Note that not every function is documented and this is simply due to the too-specific of a scenario in which the 
function was made for.

## converters

These are custom converters that you can either add as a type hint to a command, or call within a script. Not all of 
these functions should be type hinted. Converters that subclass [discord.ext.commands.Converter](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Converter) 
are the classes that can be type hinted.

***

### `class` dev.converters.CodeblockConverter
A custom converter that identifies and separates normal string arguments from codeblocks.  
Codeblock cleaning should be done later on as this does not automatically return the clean code.  
Subclass of [discord.ext.commands.Converter](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Converter).
> ### *await* convert(ctx, argument)
> The method that converts the argument passed in.
> #### Parameters
> - ctx([discord.ext.commands.Context](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context)) –
> The invocation context in which the argument is being using on.
> - argument([str](https://docs.python.org/3/library/stdtypes.html#str)) – The string that should get converted and 
> parsed.
>
> #### Returns
> Tuple[Optional[[str](https://docs.python.org/3/library/stdtypes.html#str)], Optional[[str](https://docs.python.org/3/library/stdtypes.html#str)]] – 
> A tuple with the arguments and codeblocks.

***

### `class` dev.converters.LiteralModes(modes, case_sensitive)
A custom converter that checks if a given argument falls under a [typing.Literal](https://docs.python.org/3/library/typing.html#typing.Literal) list. 
Subclass of [discord.ext.commands.Converter](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Converter).
If the given mode does not match any of the specified ones, the bot will respond with a list of available modes.
#### Example Usage
```python
@bot.command()
async def foo(ctx: commands.Context, arg: LiteralModes[typing.Literal["bar", "ABC"], True]):
     ...

@bot.command()
async def bar(ctx: commands.Context, arg: LiteralModes[typing.Literal["foo"]]):
     ...
```
#### Parameters
- modes(Literal[[str](https://docs.python.org/3/library/stdtypes.html#str)]) – The list of strings that should be 
accepted.
- case_sensitive([bool](https://docs.python.org/3/library/functions.html#bool)) – Whether the modes are 
case-sensitive. Defaults to `False`.
> ### *await* convert(ctx, mode)
> The method that converts the argument passed in.
> #### Parameters
> - ctx([discord.ext.commands.Context](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context)) –
> The invocation context in which the argument is being using on.
> - mode([str](https://docs.python.org/3/library/stdtypes.html#str)) – The string that should get checked if it falls 
> under any of the specified modes.
> #### Returns
> Optional[[str](https://docs.python.org/3/library/stdtypes.html#str)] – The mode that was accepted, if it falls under 
> any of the specified modes.

***

### *await* dev.converters.\_\_previous\_\_(ctx, command_name, arg, /)
Searches for instances of a string containing the '\_\_previous\_\_' placeholder text and replaces it with the 
contents of the last same-type command that was sent, stripping the actual command name and prefix.   
This cycle continues for a limit of 25 messages, and automatically breaks if no '\_\_previous\_\_' instance was 
found in the current message. 

This function removes codeblocks from the message if the whole message was a codeblock.

#### Parameters
- ctx([discord.ext.commands.Context](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context)) – The invocation context in which the argument is being using on.
- command_name([str](https://docs.python.org/3/library/stdtypes.html#str)) – The fully qualified command name that is being searched for. 
- arg([str](https://docs.python.org/3/library/stdtypes.html#str)) – The string that should be parsed.
#### Returns
[str](https://docs.python.org/3/library/stdtypes.html#str) – The fully parsed argument. Note that this may return the 
string without replacing '\_\_previous\_\_' if no commands where found in the last 25 messages.

***

### dev.converters.str_bool(content, default=None, *, additional_true=None, additional_false=None)
Similar to the [bool](https://docs.python.org/3/library/functions.html#bool) type hint in commands, this converts a 
string to a boolean with the added functionality of optionally appending new true/false statements.
#### Parameters
- content([str](https://docs.python.org/3/library/stdtypes.html#str)) – The string that should get converted to a
boolean.
- default(Optional[[bool](https://docs.python.org/3/library/functions.html#bool)]) – An optional boolean that gets 
returned instead of raising [discord.ext.commands.BadBoolArgument](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.BadBoolArgument) 
exception.
- additional_true(List[[str](https://docs.python.org/3/library/stdtypes.html#str)]) – A list of additional valid true 
answers.
- additional_false(List[[str](https://docs.python.org/3/library/stdtypes.html#str)]) – A list of additional valid false 
answers.
#### Returns
[bool](https://docs.python.org/3/library/functions.html#bool) – Whether the argument was considered `True` or `False` 
by the converter.
#### Raises
- [discord.ext.commands.BadBoolArgument](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.BadBoolArgument) 
– The argument that was passed could not be identified under any true or false statement.

***

### dev.converters.convert_str_to_ints(content)
Converts a string to a list of integers. 
Integer separation is determined whenever a non-numeric character appears when iterating through the characters of
`content`.
#### Parameters
- content([str](https://docs.python.org/3/library/stdtypes.html#str)) – The string that should get converted to 
integers.
#### Returns
List[[int](https://docs.python.org/3/library/functions.html#int)] – A list of the integers found in the string.

***

### dev.utils.utils.clean_code(content)
Removes any leading and trailing back ticks from a string.
#### Parameters
- content([str](https://docs.python.org/3/library/stdtypes.html#str)) – The string that should be parsed.
#### Returns
[str](https://docs.python.org/3/library/stdtypes.html#str) – The cleaned up string without any leading or trailing 
backticks.

***

### dev.utils.utils.codeblock_wrapper(content, highlight_language="")
Add leading and trailing backticks to the given string.
You can optionally add a highlight language, as well as change the highlight language if `content` were to be 
wrapped in backticks.
#### See Also
https://highlightjs.org/
#### Parameters
- content([str](https://docs.python.org/3/library/stdtypes.html#str)) – The string that should get wrapped inside 
backticks.
- highlight_language([str](https://docs.python.org/3/library/stdtypes.html#str)) – The highlight language that should 
be used.
#### Returns
[str](https://docs.python.org/3/library/stdtypes.html#str) – The parsed codeblock.

***

### dev.utils.utils.escape(content)
A helper function that combines both [discord.utils.escape_markdown](https://discordpy.readthedocs.io/en/latest/api.html#discord.utils.escape_markdown) and [discord.utils.escape_mentions](https://discordpy.readthedocs.io/en/latest/api.html#discord.utils.escape_mentions)
#### Parameters
- content([str](https://docs.python.org/3/library/stdtypes.html#str)) – The string that should be escaped.
#### Returns
[str](https://docs.python.org/3/library/stdtypes.html#str) – The cleaned up string without any markdowns or mentions.

​
​
## discord interactions

These are all functions that directly interact in some way with Discord, whether that'd be by sending messages, reacting,
or allowing pagination.

***

### `class` dev.handlers.BoolInput(author, func)
Allows the user to submit a true or false answer through buttons. 
If the user clicks on "Yes", a function is called and the view is removed.

Subclass of [discord.ui.View](https://discordpy.readthedocs.io/en/latest/api.html#discord.ui.View).
### Example Usage
```python
# inside a command
async def check():
    await ctx.send("We shall continue!")
await ctx.send("Would you like to continue?", view=BoolInput(ctx.author, check))
```
### Parameters
- author(Union[types.User, 
[int](https://docs.python.org/3/library/functions.html#int)]) – The author of the message. It can be either their ID 
or Discord object.
- func(Optional[Callable[​[], Any]]) – The function that should get called if the user clicks on the "Yes" button. 
This function cannot have arguments.

***

### `class` *async with* dev.handlers.ExceptionHandler(message, /, on_error, *, save_traceback)
Handle any exceptions in an async context manager. If any exceptions are raised during the process' lifetime, the bot 
will try to add reactions depending on the exception value.

💢 – Syntax errors (EOFError, IndentationError).  
⏰ – Timeout errors (asyncio.TimeoutError, TimeoutError).  
❓ – Reference errors (ImportError, NameError).  
❗ – Runtime errors (IndexError, KeyError, TypeError, ValueError).  
⁉ – Arithmatic errors (ZeroDivisionError, FloatingPointError).  
‼ – Any other errors that don't fall under any of the previous categories.
#### Parameters
- message([discord.Message](https://discordpy.readthedocs.io/en/latest/api.html#discord.Message)) – The message that 
the reactions will be added to.
- on_error(Callable[[], Any]) – An optional, argument-less function that is called whenever an exception is raised 
inside the context manager. This function *can* be a coroutine.
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
- scope([LocalGlobals](https://github.com/Lee-matod/dev/blob/main/docs/utils.md#class-devhandlersgloballocals__globalsnone-__localsnone-)) – The scope that will be used when dealing with variables.
#### Returns
[str](https://docs.python.org/3/library/stdtypes.html#str) – The converted string with the values of the virtual 
variables.

***

### `class` dev.pagination.Interface(paginator, author)
A paginator interface that implements basic pagination functionality.
Note that the paginator passed should have more than one page, otherwise [IndexError](https://docs.python.org/3/library/exceptions.html#IndexError) 
might be raised.

Subclass of [discord.ui.View](https://discordpy.readthedocs.io/en/latest/api.html#discord.ui.View).
#### Parameters
- paginator([Paginator](https://github.com/Lee-matod/dev/blob/main/docs/api.md#class-devpaginationpaginatorpaginator_type--prefix-suffix-max_size2000-linesepn)) – A pagination instance from which to get the pages from.
- author(Union[types.User, [int](https://docs.python.org/3/library/functions.html#int)]) – The user that should be 
able to interact with this paginator. User ID or object can be passed.
#### Attributes
- paginator([Paginator](https://github.com/Lee-matod/dev/blob/main/docs/api.md#class-devpaginationpaginatorpaginator_type--prefix-suffix-max_size2000-linesepn)) – The pagination instance that was passed to the constructor.
- author([int](https://docs.python.org/3/library/functions.html#int)) – The ID of the user that is able to interact 
with this paginator. This is the result of the user ID or object that was passed to the constructor.
> #### `property` display_page
> [str](https://docs.python.org/3/library/stdtypes.html#str) – Returns the current page of the paginator.

> #### `property` current_page
> [int](https://docs.python.org/3/library/functions.html#int) – Returns the current page number of the paginator.

***

### `class` dev.pagination.Paginator(paginator_type, *, prefix="\`\`\`", suffix="\`\`\`", max_size=2000, linesep="\n")
A [discord.ext.commands.Paginator](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Paginator) 
wrapper. This subclass deals with lines that are greater than the maximum page size by splitting them.

Subclass of [discord.ext.commands.Paginator](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Paginator).
#### See Also
[discord.ext.commands.Paginator](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Paginator)
#### Parameters
- paginator_type(Union[[discord.Embed](https://discordpy.readthedocs.io/en/latest/api.html#discord.Embed), 
[str](https://docs.python.org/3/library/stdtypes.html#str)]) – Content pagination form to use.
- prefix([str](https://docs.python.org/3/library/stdtypes.html#str)]) – From [discord.ext.commands.Paginator.prefix](https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Paginator.prefix). 
Character sequence in which all pages should start with. Defaults to '\`\`\`'.
- suffix([str](https://docs.python.org/3/library/stdtypes.html#str)]) – From [discord.ext.commands.Paginator.suffix](https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Paginator.suffix).
Character sequence in which all pages should end with. Defaults to '\`\`\`'.
- max_size([int](https://docs.python.org/3/library/functions.html#int)) – From [discord.ext.commands.Paginator.max_size](https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Paginator.max_size).
Maximum amount of characters allowed per page. Defaults to 2000.
- linesep([str](https://docs.python.org/3/library/stdtypes.html#str)]) – From [discord.ext.commands.Paginator.linesep](https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Paginator.linesep). 
Character sequence inserted between each line. Defaults to a new line ('\n').
> ### to_dict(content)
> A useful helper function that can be sent to a [discord.abc.Messageable.send](https://discordpy.readthedocs.io/en/latest/discord.abc.Messageable.send) as key-word arguments.
> #### Parameters
> - content([str](https://docs.python.org/3/library/stdtypes.html#str)) – The new content that the dictionary's value 
> should have.
> #### Returns
> Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), Union[[discord.Embed](https://discordpy.readthedocs.io/en/latest/api.html#discord.Embed), [str](https://docs.python.org/3/library/stdtypes.html#str)]] – 
> A single item dictionary with the content type as its key, and the pagination type as its value.

> ### add_line(lines="", *, empty=False)
> A wrapper to the default [discord.ext.commands.Paginator.add_line](https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Paginator.add_line). 
> Difference being that no TypeErrors are raised if the line exceeds the maximum page length.
> #### Parameters
> - line([str](https://docs.python.org/3/library/stdtypes.html#str)) – From [discord.ext.commands.Paginator.add_line](https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Paginator.add_line). 
> The line that should be added to the paginator.
> - empty([bool](https://docs.python.org/3/library/functions.html#bool)) – From [discord.ext.commands.Paginator.add_line](https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Paginator.add_line). 
> Whether an empty line should be added too.

***

### *await* dev.utils.functs.interaction_response(interaction, response_type, *args, **options)
Evaluates how to safely respond to a Discord interaction. `content`, `embed`, `embeds`, `file`, `files`, `modal` and 
`view` can all be optionally passed as positional arguments instead of keywords. 
Everything else that is available in [discord.InteractionResponse.send_message](https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.InteractionResponse.send_message)
and [discord.InteractionResponse.edit_message](https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.InteractionResponse.edit_message) 
remain as keyword arguments.
This replaces the token of the bot with '[token]' and converts any instances of a virtual variable's value back to its 
respective key. 

If a modal is passed to this function, and `response_type` is set to `InteractionResponseType.MODAL`, no other 
arguments should be passed as this will raise a [TypeError](https://docs.python.org/3/library/exceptions.html#TypeError).
#### See Also
[discord.InteractionResponse.send_message](https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.InteractionResponse.send_message), [discord.InteractionResponse.edit_message](https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.InteractionResponse.edit_message)
#### Parameters
- interaction([discord.Interaction](https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.Interaction)) – 
The interaction that should be responded to.
- response_type(types.ResponseType) – The type of response that will be used to respond to the interaction. 
[discord.InteractionResponse.defer](https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.InteractionResponse.defer) 
isn't included.
- args(Union[Sequence[Union[[discord.Embed](https://discordpy.readthedocs.io/en/latest/api.html#discord.Embed), [discord.File](https://discordpy.readthedocs.io/en/latest/api.html#discord.File)]], [discord.Embed](https://discordpy.readthedocs.io/en/latest/api.html#discord.Embed), [discord.File](https://discordpy.readthedocs.io/en/latest/api.html#discord.File), [discord.ui.View](https://discordpy.readthedocs.io/en/latest/api.html#discord.ui.View), [discord.ui.Modal](https://discordpy.readthedocs.io/en/latest/api.html#discord.ui.Modal), [str](https://docs.python.org/3/library/stdtypes.html#str)]) – 
Arguments that will be passed to [discord.InteractionResponse.send_message](https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.InteractionResponse.send_message) 
or [discord.InteractionResponse.edit_message](https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.InteractionResponse.edit_message). 
Embeds and files can be inside a list, tuple or set to send multiple of these types.
- options – Keyword arguments that will be passed to [discord.InteractionResponse.send_message](https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.InteractionResponse.send_message) 
or [discord.InteractionResponse.edit_message](https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.InteractionResponse.edit_message).
#### Raises
- [TypeError](https://docs.python.org/3/library/exceptions.html#TypeError) – Multiple arguments were passed when 
`response_type` was selected to `MODAL`, or a list, tuple or set contains more than one type.

***

### *await* dev.utils.functs.send(ctx, *args, **options)
Evaluates how to safely send a Discord message.
`content`, `embed`, `embeds`, `file`, `files` and `view` are all positional arguments instead of keywords.
Everything else that is available in [discord.ext.commands.Context.send](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context.send) 
remain as keyword arguments.

This function replaces the token of the bot with '[token]' and converts any instances of a virtual variable's value 
back to its respective key.

#### See Also
[discord.ext.commands.Context.send](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context.send)
#### Parameters
- ctx([discord.ext.commands.Context](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context)) – 
The invocation context in which the command was invoked.
- args(types.MessageContent) – Arguments that will be passed to [discord.ext.commands.Context.send](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context.send). 
Embeds and files can be inside a list, tuple or set to send multiple of these types.
- options – Keyword arguments that will be passed to [discord.ext.commands.Context.send](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context.send)
as well as the option that specifies if the message is a codeblocks.
#### Returns
Optional[[discord.Message](https://discordpy.readthedocs.io/en/latest/api.html#discord.Message)] – The message that 
was sent. This does not include pagination messages.
#### Raises
- [TypeError](https://docs.python.org/3/library/exceptions.html#TypeError) – A list, tuple or set contains more than 
one type.