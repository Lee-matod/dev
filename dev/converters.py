# -*- coding: utf-8 -*-

"""
dev.converters
~~~~~~~~~~~~~~

Custom converters used within the dev extension.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Literal, Optional, Union

import discord
from discord.ext import commands

from dev.utils.functs import flag_parser, send
from dev.utils.startup import Settings

if TYPE_CHECKING:
    from dev import types


__all__ = (
    "CodeblockConverter",
    "LiteralModes",
    "OverrideSettings",
    "str_bool",
    "str_ints"
)


class OverrideSettings(commands.Converter[None]):
    default_settings: dict[str, Any] = {}
    script: str = ""
    command_string: str = ""

    async def convert(self, ctx: commands.Context[types.Bot], argument: str) -> None:
        changed: list[str] = []
        try:
            new_settings = flag_parser(argument, "=")
        except json.JSONDecodeError:
            return
        assert isinstance(new_settings, dict)
        for key, value in new_settings.items():
            if key.startswith("__") and key.endswith("__"):
                continue
            if not hasattr(Settings, key):
                await ctx.message.add_reaction("❗")
                return
            setting = getattr(Settings, key.upper())
            if isinstance(setting, bool):
                self.default_settings[key] = str_bool(value)
                setattr(Settings, key.upper(), str_bool(value))
            elif isinstance(setting, set):
                self.default_settings[key] = set(str_ints(value))
                setattr(Settings, key.upper(), set(str_ints(value)))
            else:
                self.default_settings[key] = value
                setattr(Settings, key.upper(), value)
            changed.append(f"Settings.{key.upper()}={value}")
        await send(
            ctx,
            embed=discord.Embed(
                title="Settings Changed" if self.default_settings else "Nothing Changed",
                description="`" + '`\n`'.join(changed) + "`",
                colour=discord.Color.green() if self.default_settings else discord.Color.red()
            ),
            delete_after=5
        )
        argument = argument.strip()
        if argument.startswith("```") and argument.endswith("```"):
            self.script = argument
        else:
            self.command_string = argument

    def back_to_default(self) -> None:
        for module, value in self.default_settings.items():
            setattr(Settings, module, value)


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
        if type(item) != type(Literal[...]):  # type: ignore # noqa: E721
            raise TypeError(
                f"LiteralModes[...[, bool]] expected a typing.Literal to be passed, "
                f"not {item.__name__ if isinstance(item, type) else item.__class__.__name__}"
            )
        if any(i for i in item.__args__ if not isinstance(i, str)):
            raise TypeError("LiteralModes[...[, bool]] should only have strings")
        if not isinstance(case_sensitive, bool):  # pyright: ignore [reportUnnecessaryIsInstance]
            raise TypeError(
                f"Case sensitive argument should be a bool, "
                f"not {item.__name__ if isinstance(item, type) else item.__class__.__name__}"
            )
        return cls(item, case_sensitive)


class CodeblockConverter(commands.Converter[tuple[Optional[str], Optional[str]]]):
    """A custom converter that identifies and separates normal string arguments from codeblocks.

    Codeblock cleaning should be done later on as this does not automatically return the clean code.

    Subclass of :class:`discord.ext.commands.Converter`.
    """
    async def convert(self, ctx: commands.Context[types.Bot], argument: str) -> tuple[str | None, str | None]:
        """The method that converts the argument passed in.

        Parameters
        ----------
        ctx: :class:`Context`
            The invocation context in which the argument is being using on.
        argument: :class:`str`
            The string that should get converted and parsed.

        Returns
        -------
        Tuple[Optional[str], Optional[str]]
            A tuple with the arguments and codeblocks.
        """

        start: int | None = False

        for i in range(len(argument)):
            try:
                if "".join([argument[i], argument[i + 1], argument[i + 2]]) == "```":
                    start = i
                    break
            except IndexError:
                return argument, None
        codeblock = None
        arguments = argument[:start]
        if start is not False and argument.endswith("```"):
            if len(argument[start:]) > 3:
                codeblock = argument[start:]
            else:
                arguments = argument
        elif start is not False and not argument.endswith("```"):
            arguments = argument
        return arguments.strip() or None, codeblock


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
        default: bool | None = None, *,
        additional_true: list[str] | None = None,
        additional_false: list[str] | None = None
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
    elif str(content).lower() in false:
        return False
    elif default is not None:
        return default
    raise commands.BadBoolArgument(content)
