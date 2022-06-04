# -*- coding: utf-8 -*-

"""
dev.converters
~~~~~~~~~~~~~~

Custom converters that are used in the dev extension.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from typing import (
    List,
    Literal,
    Optional,
    Tuple
)

from discord.ext import commands

from dev.utils.utils import clean_code

__all__ = (
    "__previous__",
    "CodeblockConverter",
    "convert_str_to_bool",
    "convert_str_to_ints",
    "LiteralModes"
)


class LiteralModes(commands.Converter):
    """A custom converter that checks if a given argument falls under a typing.Literal list.

    Parameters
    ----------
    modes: :class:`Literal[...]`
        A list of modes that should be accepted.

    case_sensitive: :class:`bool`
        Whether the modes should be case-sensitive. Defaults to ``False``

    Examples
    --------
    .. codeblock:: python3
        async def foo(ctx: commands.Context, arg: LiteralModes[typing.Literal["bar", "ABC"], True]):
            ...

        async def bar(ctx: commands.Context, arg: LiteralModes[typing.Literal["foo"]]):
            ...

    Returns
    -------
    Optional[str]
        The argument that was passed if it was found in the list of acceptable modes, else None.

    Raises
    ------
    TypeError
        Invalid format was passed to the class.
    """

    def __init__(self, modes: Literal[...], case_sensitive: bool):  # type: ignore
        self.case_sensitive = case_sensitive
        if not case_sensitive:
            self.modes = [mode.lower() for mode in map(str, modes.__args__)]
        else:
            self.modes = [mode for mode in map(str, modes.__args__)]

    async def convert(self, ctx: commands.Context, mode: str) -> Optional[str]:
        if not self.case_sensitive:
            mode = mode.lower()
        if mode not in self.modes:
            valid = ", ".join(f"`{mode}`" for mode in self.modes)
            await ctx.send(f"`{mode}` is not a valid mode. Case-sensitive is {'on' if self.case_sensitive else 'off'}. Acceptable modes are:\n{valid}")
            return
        return mode

    def __class_getitem__(cls, item):
        # mostly just check that arguments were passed in correctly
        if not isinstance(item, tuple):
            item = (item, False)
        if len(item) != 2:
            raise TypeError(f"LiteralModes[...[, bool]] expected a maximum of 2 attributes, got {len(item)}")
        item, case_sensitive = item
        # can't use isinstance with typing.Literal
        if type(item) != type(Literal[...]):  # type: ignore # noqa: E721
            raise TypeError(f"LiteralModes[...[, bool]] expected a typing.Literal to be passed, not {item.__name__ if isinstance(item, type) else item.__class__.__name__}")
        if any(i for i in item.__args__ if isinstance(i, type)):
            raise TypeError("LiteralModes[...[, bool]] should only have literals, not types")
        if not isinstance(case_sensitive, bool):
            raise TypeError(f"Case sensitive argument should be a bool, not {item.__name__ if isinstance(item, type) else item.__class__.__name__}")
        return cls(item, case_sensitive)


class CodeblockConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> Tuple[str, str]:
        """A custom converter that identifies and separates normal string arguments from codeblocks.

        Codeblock cleaning should be done later on as this does not automatically return the clean code.

        Returns
        -------
        Tuple[str, str]
            A tuple with the arguments and codeblocks.
        """

        start: Optional[int] = None
        end: Optional[int] = None

        for i in range(len(argument)):
            if "".join([argument[i], argument[i + 1], argument[i + 2]]) == "```":
                start = i
            i += 1
            if "".join([argument[-i], argument[-(i + 1)], argument[-(i + 2)]]) == "```":
                end = -(i - 1) if i != 1 else None
            if start is not None and end is not None:
                break
        codeblock = argument[start:end]
        arguments = argument[:start]
        return arguments.strip(), codeblock


async def __previous__(ctx: commands.Context, code: str, /) -> str:
    previous = "__previous__"
    if "__previous__" in code:
        skip = 0  # if we don't do this, then ctx.message would be the first message and would probably break everything
        async for message in ctx.message.channel.history(limit=100):
            if skip:
                if message.author == ctx.author:
                    if message.content.startswith(f"{ctx.prefix}dev py"):
                        previous = previous.replace("__previous__", clean_code(message.content.lstrip(f"{ctx.prefix}dev py").strip()))
                    elif message.content.startswith(f"{ctx.prefix}dev python"):
                        previous = previous.replace("__previous__", clean_code(message.content.lstrip(f"{ctx.prefix}dev python").strip()))
                    if "__previous__" not in previous:
                        # No need to continue iterating through messages
                        # if '__previous__' isn't requested anymore
                        break
            else:
                skip += 1
    return code.replace("__previous__", previous)


def convert_str_to_ints(content: str) -> List[int]:
    """Converts a string to a list of integers

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
            _id = ""
    if ints.isnumeric():  # clear any extra integers
        int_list.append(int(ints))
    return int_list


def convert_str_to_bool(content: str) -> bool:
    """Similar to the :class:`bool` typehint in commands, this converts a string to a boolean.

    Parameters
    ----------
    content: :class:`str`
        The string that should get converted to a boolean.

    Returns
    -------
    bool
        Whether the argument was considered ``True`` or ``False`` by the converter.

    Raises
    ------
    commands.BadBoolArgument
        The argument that was passed could not be identified under any category.
    """
    if content.lower() in ["y", "yes", "1", "true", "t", "enable", "on"]:
        return True
    elif content.lower() in ["n", "no", "0", "false", "f", "disable", "off"]:
        return False
    else:
        raise commands.BadBoolArgument(content)
