# dev API

There are a lot of functions and classes that are used within this extension to facilitate the execution of certain 
tasks. This page focuses on documenting the numerous features that are included in the dev extension, so you can 
implement them in your own code if you'd like to.

Note that not every function is documented and this is simply due to the too-specific scenario in which the function was
made for.

***

## converters

These are custom converters that you can either add as a type hint to a command, or call within a script. Not all of 
these functions should be type hinted. Converters that subclass [Converter](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Converter) 
are the classes that can be type hinted.

> ### `class` dev.converters.CodeblockConverter
> This subclasses `discord.ext.commands.Converter`.  
> A custom converter that identifies and separates normal string arguments from codeblocks.  
> Codeblock cleaning should be done later on as this does not automatically return the clean code.  
> E.g: The second string of the returned tuple will start with and end with 3 codeblock back ticks.  
> This may return just the argument without any formatting if an IndexError is raised during runtime.
>> ### Example Usage
>> ```python
>> @bot.command()
>> async def command(ctx: commands.Context, *, args_codeblock: CodeblockConverter):
>>     arguments, codeblock = args_codeblock
>>     # do stuff
>> ```
> 
>> ### *await* convert(ctx, argument)
>> The method that converts the argument passed in.
>>> #### Parameters
>>> - ctx([Context](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context)) –
>>> The invocation context in which the argument is being using on.
>>> - argument([str](https://docs.python.org/3/library/stdtypes.html#str)) – The string that should get converted.
>>
>>> #### Returns
>>> Union[Tuple[Optional[[str](https://docs.python.org/3/library/stdtypes.html#str)], 
> Optional[[str](https://docs.python.org/3/library/stdtypes.html#str)]], [str](https://docs.python.org/3/library/stdtypes.html#str)] – 
> A tuple with the arguments and codeblocks or just the argument if IndexError was raised during parsing.
 
> ### `class` dev.converters.LiteralModes(modes, case_sensitive)
> This subclasses `discord.ext.commands.Converter`.  
> A custom converter that checks if a given argument falls under a `typing.Literal` list.  
> If the given mode does not match any of the specified ones, the bot will respond with a list of available modes.
>> #### Example Usage
>> ```python
>> @bot.command()
>> async def foo(ctx: commands.Context, arg: LiteralModes[typing.Literal["bar", "ABC"], True]):
>>      ...
>> 
>> @bot.command()
>> async def bar(ctx: commands.Context, arg: LiteralModes[typing.Literal["foo"]]):
>>      ...
>> ```
>
>> #### Parameters
>> - modes(Literal[[str](https://docs.python.org/3/library/stdtypes.html#str)]) – The modes that are acceptable.
>> - case_sensitive([bool](https://docs.python.org/3/library/functions.html#bool)) – Whether the modes are 
>> case-sensitive. Defaults to `False`.
>
>> ### *await* convert(ctx, mode)
>> The method that converts the argument passed in.
>>> #### Parameters
>>> - ctx([Context](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context)) –
>>> The invocation context in which the argument is being using on.
>>> - mode([str](https://docs.python.org/3/library/stdtypes.html#str)) – The string that should get checked if it falls 
>>> under any of the specified modes.
>>
>>> #### Returns
>>> Optional[[str](https://docs.python.org/3/library/stdtypes.html#str)] – The mode that was accepted, if it falls under 
>>> any of the specified modes.

> ### *await* dev.converters.\_\_previous\_\_(ctx, command_name, arg, /)
> Searches for instances of a string containing the '\_\_previous\_\_' placeholder text and replaces it with the contents 
> of the last same-type command that was sent stripping the actual command name and prefix.
>
> This cycle continues for a limit of 25 messages, and automatically breaks if no '\_\_previous\_\_' instance was found in 
> the current message. 
> 
> This function removes codeblocks from the message if the whole message was a codeblock.
> 
>> #### Parameters
>> - ctx([Context](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context)) – The invocation context in which the argument is being using on.
>> - command_name([str](https://docs.python.org/3/library/stdtypes.html#str)) – The fully qualified command name that is being searched for. 
>> - arg([str](https://docs.python.org/3/library/stdtypes.html#str)) – The string that should be parsed.
>
>> #### Returns
>> [str](https://docs.python.org/3/library/stdtypes.html#str) – The fully parsed argument. Note that this may return the 
>> string without replacing '\_\_previous\_\_' if no commands where found in the last 25 messages.

> ### dev.converters.convert_str_to_bool(content, default=None, *, additional_true=None, additional_false=None)
> Similar to the [bool](https://docs.python.org/3/library/functions.html#bool) typehint in commands, this converts a 
> string to a boolean with the added functionality of optionally appending new true/false statements.
>> #### Parameters
>> - content([str](https://docs.python.org/3/library/stdtypes.html#str)) – The string that should get converted to a
>> boolean.
>> - default(Optional[[bool](https://docs.python.org/3/library/functions.html#bool)]) – An optional boolean that gets 
>> returned instead of raising BadBoolArgument exception.
>> - additional_true(List[[str](https://docs.python.org/3/library/stdtypes.html#str)]) – A list of additional valid true 
>> answers.
>> - additional_false(List[[str](https://docs.python.org/3/library/stdtypes.html#str)]) – A list of additional valid false 
>> answers.
>
>> #### Returns
>> [bool](https://docs.python.org/3/library/functions.html#bool) – Whether the argument was considered `True` or `False` 
>> by the converter.
>
>> #### Raises
>> - [BadBoolArgument](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.BadBoolArgument) 
>> – The argument that was passed could not be identified under any true or false statement.

> ### dev.converters.convert_str_to_ints(content)
> Converts a string to a list of integers.  
> Integer separation is determined whenever a non-numeric character appears when iterating through the characters of 
> `content`.
>> #### Parameters
>> - content([str](https://docs.python.org/3/library/stdtypes.html#str)) – The string that should get converted to 
>> integers.
>
>> #### Returns
>> List[[int](https://docs.python.org/3/library/functions.html#int)] – A list of the integers found in the string.


> ### dev.utils.utils.clean_code(content)
> Removes any leading and trailing back ticks from a string.
> 
> Technically speaking, this just removes the first and last line of the string that was passed if it starts with and 
> ends with 3 (three) backticks.
> 
>> #### Parameters
>> - content([str](https://docs.python.org/3/library/stdtypes.html#str)) – The string that should be parsed.
>
>> #### Returns
>> [str](https://docs.python.org/3/library/stdtypes.html#str) – The cleaned up string without any leading or trailing 
>> backticks.

> ### dev.utils.utils.escape(content)
> A helper function that combines both [discord.utils.escape_markdown](https://discordpy.readthedocs.io/en/latest/api.html#discord.utils.escape_markdown) and [discord.utils.escape_mentions](https://discordpy.readthedocs.io/en/latest/api.html#discord.utils.escape_mentions)
>
>> #### Parameters
>> - content([str](https://docs.python.org/3/library/stdtypes.html#str)) – The string that should be escaped.
>
>> #### Returns
>> [str](https://docs.python.org/3/library/stdtypes.html#str) – The cleaned up string without any markdowns or mentions.


***

## discord interactions

These are all functions that directly interact in some way with Discord, whether that'd be by sending messages, reacting,
or allowing pagination.

> ### `class` dev.handlers.BoolInput(author, func, *args, **kwargs)
> Allows the user to submit a yes or no answer through buttons. If the user clicks on yes, a function is called and the 
> view is removed.
>> ### Example Usage
>> ```python
>> async def check(ctx: commands.Context):
>>     await ctx.send("We shall continue!")
>> await ctx.send("Would you like to continue?", view=BoolInput(ctx.author, check, ctx))
>> ```
>
>> ### Parameters
>> - author(Union[[abc.User](https://discordpy.readthedocs.io/en/latest/api.html#discord.abc.User), 
>> [int](https://docs.python.org/3/library/functions.html#int)]) – The author of the message. It can be either their ID 
>> or User object.
>> - func(Callable[Any, Any]) – The function that should get called if the user clicks on the yes button.
>> - args – The arguments that should be passed into the function once it gets executed, if any.
>> - kwargs – The keyword arguments that should be passed into the function once it gets executed, if any.

> ### `class` *async with* dev.handlers.ExceptionHandler(message, /, on_error, *, save_traceback)
> Handle any exceptions in an async context manager.
>  If any exceptions are raised during the process' lifetime, the bot will try to add
>   reactions depending on the exception value.
>
> 💢 – Syntax errors (EOFError, IndentationError).  
> ⏰ – Timeout errors (asyncio.TimeoutError, TimeoutError).  
> ❓ – Reference errors (ImportError, NameError).  
> ❗ – Runtime errors (IndexError, KeyError, TypeError, ValueError).  
> ⁉ – Arithmatic errors (ZeroDivisionError, FloatingPointError).  
> ‼ – Any other errors that don't fall under any of the previous categories.
>> #### Parameters
>> - message([Message](https://discordpy.readthedocs.io/en/latest/api.html#discord.Message)) – The message that the 
>> reactions will be added to.
>> - on_error(Callable[[], Any]) – An optional, argument-less function that is called whenever an exception is raised 
>> inside the context manager. This function *can* be a coroutine.
>> - save_traceback([bool](https://docs.python.org/3/library/functions.html#bool)) – Whether to save a traceback if an 
>> exception is raised. Defaults to ``False``.
>
>> #### `classmethod` cleanup
>> Deletes any tracebacks that were saved if `send_traceback` was set to `True`.  
>> This method should always get called once you have finished handling any tracebacks

> ### `class` dev.handlers.Paginator(paginator, owner, *, embed)
> This subclasses `discord.ui.View`.  
> A paginator interface that allows you to iterate through pages if a message exceeds character limits using buttons.
>> #### Example Usage
>> ```python
>> paginator = commands.Paginator(...)
>> for line in some_long_text.split("\n"):
>>     paginator.add_line(line)
>> interface = dev.Paginator(paginator, ctx.author.id)
>> await ctx.send(interface.pages[0], view=interface)
>>```
>
>> #### Parameters
>> - paginator([Paginator](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#paginator)) – The paginator
>> class from where to get the pages from.
>> - owner([int](https://docs.python.org/3/library/functions.html#int)) – The ID of the author of the command's invoked 
>> message.
>> - embed([Embed](https://discordpy.readthedocs.io/en/latest/api.html#embed)) – If the message is an embed, then the 
>> embed should be passed here.

> ### dev.handlers.replace_vars(string)
> Replaces any instance of a virtual variables with their respective values and return it the parsed string.
> 
> Instances of the variables will not get converted if a value is not found.
>> #### Parameters
>> - string([str](https://docs.python.org/3/library/stdtypes.html#str)) – The string that should get converted.
>
>> #### Returns
>> [str](https://docs.python.org/3/library/stdtypes.html#str) – The converted string with the values of the virtual 
>> variables.

> ### *await* dev.utils.functs.send(ctx, *args, **options)
> Evaluates how to safely send a discord message.  
> `content`, `embed`, `embeds`, `file`, `files` and `view` are all positional arguments instead of keywords.
> Everything else that is available in [discord.ext.commands.Context.send](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context.send) 
> remain as keyword arguments.
>
> This replaces the bot's token with '[token]' and converts any instances of a virtual variable's value back to its 
> respective key.
>
>> #### See Also
>> [discord.ext.commands.Context.send](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context.send) – 
>> View a list of all possible arguments and keyword arguments that are available to be passed into this function.
> 
>> #### Parameters
>> - ctx([Context](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context)) – The 
>> invocation context in which the command was invoked.
>> - args(Union[Sequence[Union[[Embed](https://discordpy.readthedocs.io/en/latest/api.html#discord.Embed), [File](https://discordpy.readthedocs.io/en/latest/api.html#discord.File)]], [Embed](https://discordpy.readthedocs.io/en/latest/api.html#discord.Embed), [File](https://discordpy.readthedocs.io/en/latest/api.html#discord.File), [View](https://discordpy.readthedocs.io/en/latest/api.html#discord.ui.View), [str](https://docs.python.org/3/library/stdtypes.html#str)]) – 
>> Arguments that will be passed to [Context.send](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context.send). 
>> Embeds and files can be inside a list, tuple or set to send multiple of these types.
>> - options – Keyword arguments that will be passed to [Context.send](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Context.send)
>> as well as the option that specifies if the message is a codeblocks.
>
>> #### Returns
>> Optional[[Message](https://discordpy.readthedocs.io/en/latest/api.html#discord.Message)] – The message that was sent. 
>> This does not include pagination messages.
> 
>> #### Raises
>> [TypeError](https://docs.python.org/3/library/exceptions.html#TypeError) – A list, tuple or set contains more than 
>> one type, e.g: [File, File, Embed].


