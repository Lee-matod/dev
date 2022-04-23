# -*- coding: utf-8 -*-

"""
dev.converters
~~~~~~~~~~~~~~

Custom converters that are used in the dev extension.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""

from typing import *

from discord.ext import commands

from dev.utils.functs import clean_code


__all__ = (
    "__previous__",
    "StringCodeblockConverter",
    "convert_str_to_bool",
    "convert_str_to_ids",
    "plural"
)


class StringCodeblockConverter(commands.Converter):
    """A custom converter that identifies and separates normal string args and codeblocks.

    Codeblock cleaning should be done later on as this does not automatically return the clean code.

    Returns
    -------
    Tuple[str, str]
        A tuple with index position 0 being the arguments, and index position 1 being the codeblock.
    """

    async def convert(self, ctx: commands.Context, argument: str) -> Tuple[str, str]:
        start: Optional[int] = None
        end: Optional[int] = None

        for i in range(len(argument)):
            if "".join([argument[i], argument[i + 1], argument[i + 2]]) == "```":
                if start is None and end is None:
                    start = i
                elif end is None and start is not None:
                    end = i + 3
                    break
        codeblock = argument[start:end]
        arguments = argument[:start]
        return arguments.strip(), codeblock


async def __previous__(ctx: commands.Context, code: str, /):
    previous = code
    if "__previous__" in code:
        skip = 0  # if we don't do this, then ctx.message would be the first message and would probably break everything
        async for message in ctx.message.channel.history(limit=200):
            if skip:
                if message.author == ctx.author:
                    if message.content.startswith(f"{ctx.prefix}dev py"):
                        previous = previous.replace("__previous__", clean_code(message.content.lstrip(f"{ctx.prefix}dev py").strip()))
                    if message.content.startswith(f"{ctx.prefix}dev python"):
                        previous = previous.replace("__previous__", clean_code(message.content.lstrip(f"{ctx.prefix}dev python").strip()))
                    if "__previous__" not in previous:
                        # No need to continue iterating through messages
                        # if '__previous__' isn't requested anymore
                        break
            else:
                skip += 1
    return previous


def plural(amount: int, singular: str) -> str:
    if amount == 1:
        return f"{amount} {singular}"
    else:
        return f"{amount} {singular}s"


def convert_str_to_ids(content: str) -> List[str]:
    id_list: List[str] = []
    _id: str = ""
    for char in content:
        if char.isnumeric():
            _id += char
        if not char.isnumeric() and _id:
            id_list.append(_id)
            _id = ""
    if _id.isnumeric():
        id_list.append(_id)
    return id_list


def convert_str_to_bool(content: str) -> bool:
    if content.lower() in ["y", "yes", "1", "true", "t", "enable", "on"]:
        return True
    elif content.lower() in ["n", "no", "0", "false", "f", "disable", "off"]:
        return False
    else:
        raise commands.BadBoolArgument(content)