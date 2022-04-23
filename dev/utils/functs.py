# -*- coding: utf-8 -*-

"""
dev.utils.functs
~~~~~~~~~~~~~~~

Basic functions that will be used with the dev extension.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from typing import *

import io

import discord

from copy import copy
from typing import TextIO
from discord.ext import commands

from dev.utils.startup import settings
from dev.utils.baseclass import Paginator
from dev.utils.utils import local_globals


__all__ = (
    "clean_code",
    "generate_ctx",
    "is_owner",
    "send"
)


async def send(ctx: commands.Context, content: Optional[str] = None, *, is_py_bt: bool = False, **options) -> discord.Message:
    """Evaluates how to send a discord message.

    Parameters
    ----------
    ctx: :class:`commands.Context`
        The context in which the command was invoked on.
    content: Optional[:class:`str`]
        The contents that the message should include.
    is_py_bt: :class:`bool`
        Whether the contents of the message are inside a Python codeblock.
    options:
        Additional key-word arguments that will be sent to ctx.send.

    Returns
    -------
    discord.Message
        The message that was sent. This does not include Pagination messages.
    """
    kwargs = {**options}
    content = str(content).replace(ctx.bot.http.token, "TOKEN") if content else None

    if content:
        content = _revert_virtual_var_value(content)
        if not isinstance(content, (discord.Embed, discord.File, TextIO)):
            if len(content) > 3990:
                paginator = commands.Paginator(prefix="```py\n", suffix="```\n")
                for line in content.split("\n"):
                    paginator.add_line(line.replace("`", "\u200b`"))
                await ctx.send(paginator.pages[0], view=Paginator(paginator, ctx.author.id))
            else:
                if is_py_bt:
                    replacement = content.replace("`", "\u200b`")
                    content = f'```py\n{replacement}\n```'
                kwargs["content"] = content

    for _type, _content in options.items():
        if isinstance(_content, discord.File):
            string = _revert_virtual_var_value("".join(_content.fp.readlines()).replace(ctx.bot.http.token, "TOKEN")).encode("utf-8")
            kwargs["file"] = discord.File(filename=_content.filename, fp=io.BytesIO(string))

        elif isinstance(_content, discord.Embed):
            _content.description = _content.description.replace(ctx.bot.http.token, "TOKEN")
            _content.description = _revert_virtual_var_value(_content.description)
            if len(_content.description) > 4085:
                paginator = commands.Paginator(prefix="```py\n", suffix="```\n")
                for line in _content.description.split("\n"):
                    paginator.add_line(line.replace("`", "\u200b`"))
                _content.description = _content.description = paginator.pages[0]
                await ctx.send(embed=_content, view=Paginator(paginator, ctx.author.id))
            else:
                if is_py_bt:
                    replacement = _content.description.replace("`", "\u200b`")
                    _content.description = f'```py\n{replacement}\n```'
                kwargs["embed"] = _content
    if kwargs:
        return await ctx.send(**kwargs)


def _revert_virtual_var_value(string: str) -> str:
    # For security reasons, when using await send(), this gets automatically called
    for var_name, var_value in local_globals.items():
        if var_value in string:
            string = string.replace(var_value, var_name)
    return string


async def generate_ctx(ctx: commands.Context, author: discord.Member, channel: discord.TextChannel, **kwargs) -> commands.Context:
    """Create a custom context with changeable attributes.

    Parameters
    ----------
    ctx: :class:`commands.Context`
        The default context in which the command was invoked on.
    author: :class:`discord.Memeber`
        A new author that the generated context should have.
    channel: :class:`discord.TextChannel`
        A new text channel that the generated context should have.
    kwargs:
        Any other additional attributes that the genereated context should have.

    Returns
    -------
    commands.Context
        A newly created context.
    """
    alt_msg: discord.Message = copy(ctx.message)
    alt_msg._update(kwargs)
    alt_msg.author = author
    alt_msg.channel = channel
    return await ctx.bot.get_context(alt_msg, cls=type(ctx))


def is_owner() -> Callable:
    def owner(ctx: commands.Context) -> bool:
        if settings["owners"]:
            if ctx.author.id in settings["owners"]:
                return True
            raise commands.NotOwner("You either do not own this bot or are not listed in the override owner list.")
        elif ctx.author.id in ctx.bot.owner_ids or ctx.author.id == ctx.bot.owner_id:
            return True
        raise commands.NotOwner("You either do not own this bot or are not listed in the override owner list.")
    return commands.check(owner)


def clean_code(content: str) -> str:
    """Clean any codeblock arguments.

    If no codeblocks are found, then it will simply return the normal string without any changes made.

    Example
    -------
    Simple string in between backticks (codeblocks) converted to a clean string without any back ticks
    .. code-block:: python3
        codeblock: str = "```py" \
                   "print('Hello World!')" \
                   "```"
        clean_codeblock = clean_code(codeblock)
        print(clean_codeblock)

    Parameters
    ----------
    content: :class:`str`
        The string that should get cleaned.

    Returns
    -------
    str
        The cleaned string without any backticks
    """
    if content.startswith("```") and content.endswith("```"):
        return "\n".join(content.split("\n")[1:-1])
    else:
        return content
