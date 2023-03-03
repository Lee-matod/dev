# -*- coding: utf-8 -*-

"""
dev.converters
~~~~~~~~~~~~~~

Custom converters used within the dev extension.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import collections
import re
from typing import TYPE_CHECKING, Any, Deque, Literal, TypeVar, Union

import discord
from discord.ext import commands

from dev.utils.utils import clean_code, codeblock_wrapper

if TYPE_CHECKING:
    from dev import types

__all__ = (
    "GlobalTextChannelConverter",
    "LiteralModes",
    "MessageCodeblock",
    "codeblock_converter",
    "str_bool",
    "str_ints",
)

T = TypeVar("T")


class GlobalTextChannelConverter(commands.TextChannelConverter):
    """Similar to :class:`discord.ext.commands.TextChannelConverter`, but convert channels client-wide instead of
    guild-wide.
    """

    async def convert(self, ctx: commands.Context[types.Bot], argument: str) -> discord.TextChannel:
        try:
            channel = await super().convert(ctx, argument)
        except commands.ChannelNotFound as exc:
            match = re.match(r"<#([0-9]{15,20})>$", argument)
            if argument.isnumeric():
                channel = ctx.bot.get_channel(int(argument))
            elif match is not None:
                channel = ctx.bot.get_channel(int(match.group(1)))
            else:
                raise exc
        if channel is None:
            raise commands.ChannelNotFound(argument)
        return channel  # type: ignore


class LiteralModes(commands.Converter[Union[str, None]]):
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

    def __init__(self, modes: Literal[...], case_sensitive: bool) -> None:  # type: ignore
        self.case_sensitive: bool = case_sensitive
        if not case_sensitive:
            self.modes: list[str] = [mode.lower() for mode in map(str, modes.__args__)]  # type: ignore
        else:
            self.modes: list[str] = list(map(str, modes.__args__))  # type: ignore

    async def convert(self, ctx: commands.Context[types.Bot], argument: str) -> str | None:
        """The method that converts the argument passed in.

        Parameters
        ----------
        ctx: :class:`Context`
            The invocation context in which the argument is being using on.
        argument: :class:`str`
            The string that should get checked if it falls under any of the specified modes.

        Returns
        -------
        Optional[str]
            The mode that was accepted, if it falls under any of the specified modes.
        """
        is_upper: bool = argument.isupper()
        if not self.case_sensitive:
            argument = argument.lower()
        if argument not in self.modes:
            valid = ", ".join(f"`{mode}`" for mode in self.modes)
            await ctx.send(
                f"`{argument}` is not a valid mode. "
                f"Case-sensitive is {'enabled' if self.case_sensitive else 'disabled'}. Acceptable modes are: {valid}"
            )
            return
        return argument.upper() if is_upper else argument

    def __class_getitem__(cls, item: Any) -> LiteralModes:  # type: ignore
        # mostly just check that arguments were passed in correctly
        if not isinstance(item, tuple):
            item = (item, False)
        if len(item) != 2:  # type: ignore
            raise TypeError(
                f"LiteralModes[...[, bool]] expected a maximum of 2 attributes, got {len(item)}"  # type: ignore
            )
        item, case_sensitive = item
        item: Any
        case_sensitive: bool
        if type(item) != type(Literal[...]):  # type: ignore
            raise TypeError(
                f"LiteralModes[...[, bool]] expected a typing.Literal to be passed, "
                f"not {item.__name__ if isinstance(item, type) else item.__class__.__name__}"
            )
        if any(i for i in item.__args__ if not isinstance(i, str)):
            raise TypeError("LiteralModes[...[, bool]] should only have strings")
        if not isinstance(case_sensitive, bool):
            raise TypeError(
                f"Case sensitive argument should be a bool, "
                f"not {item.__name__ if isinstance(item, type) else item.__class__.__name__}"
            )
        return cls(item, case_sensitive)


class MessageCodeblock:
    """Represents a Discord message with a codeblock.
    
    Attributes
    ----------
    content: :class:`str`
        Any arguments outside of the codeblock.
    codeblock: Optional[:class:`str`]
        The contents of codeblock, if any. Does not include backticks nor highlight language.
    highlightjs: Optional[:class:`str`]
        The highlight language of the codeblock, if any.
    """

    def __init__(self, content: str, codeblock: str | None, highlightjs: str | None) -> None:
        self.content: str = content
        self.codeblock: str | None = clean_code(codeblock) if codeblock is not None else None
        self.lang: str | None = highlightjs

    def __str__(self) -> str:
        """Returns a completed string with all components of the message combined."""
        if self.codeblock and self.lang:
            return f"{self.content} {codeblock_wrapper(self.codeblock, self.lang)}"
        return self.content


def codeblock_converter(content: str) -> MessageCodeblock:
    """A custom converter that identifies and separates normal string arguments from codeblocks.

    Parameters
    ----------
    content: :class:`str`
        The string that should be parsed.

    Returns
    -------
    MessageCodeblock
        The divided message as a useful pythonic object.
    """
    start: int | None = None
    lang: int | None = None
    last_seen: Deque[str] = collections.deque(maxlen=3)

    for idx, char in enumerate(content):
        last_seen.append(char)
        if start is None and "".join(last_seen) == "```":
            #  With this we know where the codeblock starts.
            #  Likewise, we know where the argument will end.
            start = idx - 2
        if start is not None and char == "\n":
            #  Now that we know we're actually in the codeblock,
            #  we can find out which language was being used.
            #  This also means that we can break out, because
            #  everything else is of no use to us.
            lang = idx
            break
    hljs: str | None = None
    codeblock: str | None = None
    if start is not None and lang is not None:
        hljs = content[start + 3 : lang].strip()
    if lang is not None:
        cleaned_initial = content[lang + 1 :].strip()
        if cleaned_initial.endswith("```"):
            codeblock = cleaned_initial[:-3].strip("\n")
    return MessageCodeblock(content[:start].strip(), codeblock, hljs)


def str_ints(content: str) -> list[int]:
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
    int_list: list[int] = []
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
    default: bool | None = None,
    *,
    additional_true: list[str] | None = None,
    additional_false: list[str] | None = None,
) -> bool:
    """Similar to the :class:`bool` type hint in commands, this converts a string to a boolean with the added
    functionality of optionally appending new true/false statements.

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
    true = ["y", "yes", "1", "true", "t", "enable", "on"]
    false = ["n", "no", "0", "false", "f", "disable", "off"]
    if additional_true is not None:
        true.extend(additional_true)
    if additional_false is not None:
        false.extend(additional_false)
    if str(content).lower() in true:
        return True
    if str(content).lower() in false:
        return False
    if default is not None:
        return default
    raise commands.BadBoolArgument(content)
