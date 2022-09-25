# -*- coding: utf-8 -*-

"""
dev.converters
~~~~~~~~~~~~~~

Custom converters used within the dev extension.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from typing import List, Literal, Optional, Tuple, Union

from discord.ext import commands

from dev.utils.utils import clean_code

__all__ = (
    "__previous__",
    "CodeblockConverter",
    "str_bool",
    "str_ints",
    "LiteralModes"
)


class LiteralModes(commands.Converter):
    """A custom converter that checks if a given argument falls under a typing.Literal list.

    Subclass of :class:`discord.ext.commands.Converter`.

    Examples
    --------
    .. codeblock:: python3

        @bot.command()
        async def foo(ctx: commands.Context, arg: LiteralModes[typing.Literal["bar", "ABC"], True]):
            ...

        @bot.command()
        async def bar(ctx: commands.Context, arg: LiteralModes[typing.Literal["foo"]]):
            ...

    Parameters
    ----------
    modes: :class:`Literal[...]`
        The list of strings that should be accepted.

    case_sensitive: :class:`bool`
        Whether the modes should be case-sensitive. Defaults to `False`
    """

    def __init__(self, modes: Literal[...], case_sensitive: bool):  # type: ignore
        self.case_sensitive: bool = case_sensitive
        if not case_sensitive:
            self.modes: List[str] = [mode.lower() for mode in map(str, modes.__args__)]
        else:
            self.modes: List[str] = list(map(str, modes.__args__))

    async def convert(self, ctx: commands.Context, mode: str) -> Optional[str]:
        """The method that converts the argument passed in.

        Parameters
        ----------
        ctx: :class:`Context`
            The invocation context in which the argument is being using on.
        mode: :class:`str`
            The string that should get checked if it falls under any of the specified modes.

        Returns
        -------
        Optional[str]
            The mode that was accepted, if it falls under any of the specified modes.
        """

        if not self.case_sensitive:
            mode = mode.lower()
        if mode not in self.modes:
            valid = ", ".join(f"`{mode}`" for mode in self.modes)
            await ctx.send(
                f"`{mode}` is not a valid mode."
                f"Case-sensitive is {'enabled' if self.case_sensitive else 'disabled'}. Acceptable modes are: {valid}"
            )
            return
        return mode

    def __class_getitem__(cls, item):
        # mostly just check that arguments were passed in correctly
        if not isinstance(item, tuple):
            item = (item, False)
        if len(item) != 2:
            raise TypeError(f"LiteralModes[...[, bool]] expected a maximum of 2 attributes, got {len(item)}")
        item, case_sensitive = item
        if type(item) != type(Literal[...]):  # type: ignore # noqa: E721
            raise TypeError(
                f"LiteralModes[...[, bool]] expected a typing.Literal to be passed, "
                f"not {item.__name__ if isinstance(item, type) else item.__class__.__name__}"
            )
        if any(i for i in item.__args__ if isinstance(i, type)):
            raise TypeError("LiteralModes[...[, bool]] should only have literals, not types")
        if not isinstance(case_sensitive, bool):
            raise TypeError(
                f"Case sensitive argument should be a bool, "
                f"not {item.__name__ if isinstance(item, type) else item.__class__.__name__}"
            )
        return cls(item, case_sensitive)


class CodeblockConverter(commands.Converter):
    """A custom converter that identifies and separates normal string arguments from codeblocks.

    Codeblock cleaning should be done later on as this does not automatically return the clean code.

    Subclass of :class:`discord.ext.commands.Converter`.
    """
    async def convert(self, ctx: commands.Context, argument: str) -> Union[Tuple[Optional[str], Optional[str]], str]:
        """The method that converts the argument passed in.

        Parameters
        ----------
        ctx: :class:`Context`
            The invocation context in which the argument is being using on.
        argument: :class:`str`
            The string that should get converted and parsed.

        Returns
        -------
        Union[Tuple[Optional[str], Optional[str]], str]
            A tuple with the arguments and codeblocks or just the argument if IndexError was raised during parsing.
        """

        start: Optional[int] = False
        end: Optional[int] = False

        for i in range(len(argument)):
            try:
                if "".join([argument[i], argument[i + 1], argument[i + 2]]) == "```":
                    start = i
                i += 1
                if "".join([argument[-i], argument[-(i + 1)], argument[-(i + 2)]]) == "```":
                    end = -(i - 1) if i != 1 else None
                if start is not False and end is not False:
                    break
            except IndexError:
                return argument
        codeblock = argument[start:end]
        arguments = argument[:start]
        return arguments.strip(), codeblock


async def __previous__(ctx: commands.Context, command_name: str, arg: str, /) -> str:
    """Searches for instances of a string containing the '__previous__' placeholder text and
    replaces it with the contents of the last same-type command that was sent, stripping the
    actual command name and prefix.

    This cycle continues for a limit of 25 messages, and automatically breaks if no
    '__previous__' instance was found in the current message.

    This function removes codeblocks from the message if the whole message was a codeblock.

    Parameters
    ----------
    ctx: :class:`commands.Context`
        The invocation context in which the argument is being using on.
    command_name: :class:`str`
        The fully qualified command name that is being searched for.
    arg: :class:`str`
        The string that should be parsed.

    Returns
    -------
    str
        The fully parsed argument. Note that this may return the string without replacing '__previous__'
        if no commands where found in the last 25 messages.
    """

    previous = "__previous__"
    if "__previous__" in arg:
        skip = 0  # if we don't do this, then ctx.message would be the first message and would probably break everything
        async for message in ctx.message.channel.history(limit=25):
            if skip:
                if message.author == ctx.author:
                    if message.content.startswith(f"{ctx.prefix}{command_name}"):
                        previous = previous.replace(
                            "__previous__",
                            clean_code(message.content.lstrip(f"{ctx.prefix}{command_name}").strip())
                        )
                    if "__previous__" not in previous:
                        # No need to continue iterating through messages
                        # if '__previous__' isn't requested anymore
                        break
            else:
                skip += 1
    return arg.replace("__previous__", previous)


def str_ints(content: str) -> List[int]:
    """Converts a string to a list of integers.
    Integer separation is determined whenever a non-numeric character appears when iterating through the characters of
    `content`.

    Parameters
    ----------
    content: :class:`str`
        The string that should get converted to integers.

    Returns
    -------
    List[int]
        A list of the integers found in the string.
    """
    int_list: List[int] = []
    ints: str = ""
    for char in content:
        if char.isnumeric():
            ints += char
        if not char.isnumeric() and ints:
            int_list.append(int(ints))
            ints = ""
    if ints.isnumeric():  # clear any extra integers
        int_list.append(int(ints))
    return int_list


def str_bool(
        content: str,
        default: Optional[bool] = None, *,
        additional_true: Optional[List[str]] = None,
        additional_false: Optional[List[str]] = None
) -> bool:
    """Similar to the :class:`bool` type hint in commands, this converts a string to a boolean
    with the added functionality of optionally appending new true/false statements.

    Parameters
    ----------
    content: :class:`str`
        The string that should get converted to a boolean.
    default: Optional[:class:`bool`]
        An optional boolean that gets returned instead of raising BadBoolArgument exception.
    additional_true: Optional[List[:class:`str`]]
        A list of additional valid true answers.
    additional_false: Optional[List[:class:`str`]]
        A list of additional valid false answers.

    Returns
    -------
    bool
        Whether the argument was considered `True` or `False` by the converter.

    Raises
    ------
    BadBoolArgument
        The argument that was passed could not be identified under any true or false statement.
    """
    additional_true: List[str] = [t.lower() for t in additional_true] or []
    additional_false: List[str] = [f.lower() for f in additional_false] or []
    if str(content).lower() in ["y", "yes", "1", "true", "t", "enable", "on", *additional_true]:
        return True
    elif str(content).lower() in ["n", "no", "0", "false", "f", "disable", "off", *additional_false]:
        return False
    elif default is not None:
        return default
    else:
        raise commands.BadBoolArgument(content)
