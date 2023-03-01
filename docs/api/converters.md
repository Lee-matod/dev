# converters

These are custom converters that you can either add as a type hint to a command, or call within a script.

***

### `class` dev.converters.MessageCodeblock(content, codeblock, highlightjs)

Represents a Discord message with a codeblock.

#### Attributes
content([str](https://docs.python.org/3/library/stdtypes.html#str)]) – Any arguments outside of the codeblock.
codeblock(Optional[[str](https://docs.python.org/3/library/stdtypes.html#str)]) – The contents of codeblock, if any.
  Does not include backticks nor highlight language.
highlightjs(Optional[[str](https://docs.python.org/3/library/stdtypes.html#str)]) – The highlight language of the
  codeblock, if any.

> ### Supported Operations
>> #### str(x)
>> Returns a completed string with all components of the message combined.

***

### `class` dev.converters.LiteralModes(modes, case_sensitive)

A custom converter that checks if a given argument falls under
a [typing.Literal](https://docs.python.org/3/library/typing.html#typing.Literal) list.

Subclass
of [discord.ext.commands.Converter](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Converter).

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

### dev.converters.codeblock_converter(content)

A custom converter that identifies and separates normal string arguments from codeblocks.

#### Paramters
- content([str](https://docs.python.org/3/library/stdtypes.html#str)) – The string that should be parsed.

#### Returns
[MessageCodeblock](https://github.com/Lee-matod/dev/blob/main/docs/api/converters.md#class-devconvertersmessagecodeblockcontent-codeblock-highlightjs) –
  The divided message as a useful pythonic object.

***

### dev.converters.str_bool(content, default=None, *, additional_true=None, additional_false=None)

Similar to the [bool](https://docs.python.org/3/library/functions.html#bool) type hint in commands, this converts a
string to a boolean with the added functionality of optionally appending new true/false statements.

#### Parameters

- content([str](https://docs.python.org/3/library/stdtypes.html#str)) – The string that should get converted to a
  boolean.
- default(Optional[[bool](https://docs.python.org/3/library/functions.html#bool)]) – An optional boolean that gets
  returned instead of
  raising [discord.ext.commands.BadBoolArgument](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.BadBoolArgument)
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

### dev.converters.str_ints(content)

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

A helper function that combines
both [discord.utils.escape_markdown](https://discordpy.readthedocs.io/en/latest/api.html#discord.utils.escape_markdown)
and [discord.utils.escape_mentions](https://discordpy.readthedocs.io/en/latest/api.html#discord.utils.escape_mentions)

#### Parameters

- content([str](https://docs.python.org/3/library/stdtypes.html#str)) – The string that should be escaped.

#### Returns

[str](https://docs.python.org/3/library/stdtypes.html#str) – The cleaned up string without any markdowns or mentions.
