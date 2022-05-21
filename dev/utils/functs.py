# -*- coding: utf-8 -*-

"""
dev.utils.functs
~~~~~~~~~~~~~~~

Basic functions that will be used with the dev extension.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""


from typing import (
    Any,
    Dict,
    List,
    Sequence,
    Union
)

import discord
import io

from discord.ext import commands
from copy import copy

from dev.handlers import Paginator

from dev.utils.utils import local_globals


__all__ = (
    "clean_code",
    "generate_ctx",
    "send",
    "table_creator"
)


def table_creator(rows: List[List[Any]], labels: List[str]) -> str:
    table: List[Dict[Any, List[Any]]] = []
    table_str = ""
    for label in labels:
        if label == "Types":
            label = " Types "
        table.append({label: []})

    for row in rows:
        num, _type, desc = row
        id_lab, type_lab, desc_lab = list(table[0].keys())[0], list(table[1].keys())[0], list(table[2].keys())[0]
        table[0][id_lab].append(num)
        table[1][type_lab].append(_type)
        table[2][desc_lab].append(desc)
    table_str += "  │  ".join(list(label.keys())[0] for label in table)
    length = ""
    for char in table_str:
        if char == "│":
            length += "┼"
        else:
            length += "─"
    table_str += f"\n{length}\n"
    for row in rows:
        num = f"{' ' * (3 - len(str(row[0])))}{str(row[0])}"
        table_str += "  │  ".join([num, row[1], row[2]])
        table_str += f"\n{length}\n"
    return "\n".join(table_str.split("\n")[:-2])


async def send(ctx: commands.Context, *args: Union[Sequence[Union[discord.Embed, discord.File]], discord.Embed, discord.File, discord.ui.View, str], **options: bool) -> Union[discord.Message, Dict[str, Any]]:
    """Evaluates how to send a discord message.

    Parameters
    ----------
    ctx: :class:`commands.Context`
        The context in which the command was invoked on.
    args:
        Additional arguments that will be sent to :meth:`ctx.send`.

    Returns
    -------
    discord.Message
        The message that was sent. This does not include Pagination messages.
    """
    py_codeblock = options.get("py_codeblock", False)
    kwargs = {}
    for arg in args:
        if isinstance(arg, discord.Embed):
            if arg.description:
                arg.description = arg.description.replace(ctx.bot.http.token, "TOKEN")
                arg.description = _revert_virtual_var_value(arg.description)
                if len(arg.description) > 4085:
                    paginator = commands.Paginator(prefix="```py\n", suffix="```\n")
                    for line in arg.description.split("\n"):
                        paginator.add_line(line.replace("`", "\u200b`"))
                    arg.description = paginator.pages[0]
                    await ctx.send(embed=arg, view=Paginator(paginator, ctx.author.id))
                else:
                    if py_codeblock:
                        replacement = arg.description.replace("`", "\u200b`")
                        arg.description = f'```py\n{replacement}\n```'
                    if kwargs.get("embed", False):
                        other_embed = kwargs.pop("embed")
                        kwargs["embeds"] = [other_embed, arg]
                    elif kwargs.get("embeds", False):
                        kwargs["embeds"].append(arg)
                    else:
                        kwargs["embed"] = arg
            else:
                if kwargs.get("embed", False):
                    other_embed = kwargs.pop("embed")
                    kwargs["embeds"] = [other_embed, arg]
                elif kwargs.get("embeds", False):
                    kwargs["embeds"].append(arg)
                else:
                    kwargs["embed"] = arg

        elif isinstance(arg, discord.File):
            string = _revert_virtual_var_value("".join(line.decode('utf-8') for line in arg.fp.readlines()).replace(ctx.bot.http.token, "TOKEN")).encode('utf-8')
            if kwargs.get("file", False):
                file = kwargs.pop("file")
                kwargs["files"] = [file, discord.File(filename=f"{arg.filename}.txt" if "." not in arg.filename else arg.filename, fp=io.BytesIO(string))]
            elif kwargs.get("files", False):
                kwargs["files"].append(string)
            else:
                kwargs["file"] = discord.File(filename=f"{arg.filename}.txt" if "." not in arg.filename else arg.filename, fp=io.BytesIO(string))

        elif isinstance(arg, (list, set, tuple)):
            items = []
            str_type = ""
            inst_type = None
            for item in arg:
                if isinstance(item, discord.File):
                    if inst_type:
                        if not isinstance(item, inst_type):
                            raise ValueError
                    str_type = "files"
                    inst_type = discord.File
                    string = _revert_virtual_var_value("".join(line.decode('utf-8') for line in item.fp.readlines()).replace(ctx.bot.http.token, "TOKEN")).encode('utf-8')
                    items.append(discord.File(filename=f"{item.filename}.txt" if "." not in item.filename else item.filename, fp=io.BytesIO(string)))
                elif isinstance(item, discord.Embed):
                    if inst_type:
                        if not isinstance(item, inst_type):
                            raise ValueError
                    str_type = "embeds"
                    inst_type = discord.Embed
                    if item.description:
                        item.description = _revert_virtual_var_value(item.description.replace(ctx.bot.http.token, "TOKEN"))
                        if len(item.description) > 4085:
                            paginator = commands.Paginator(prefix="```py\n", suffix="```\n")
                            for line in item.description.split("\n"):
                                paginator.add_line(line.replace("`", "\u200b`"))
                            item.description = paginator.pages[0]
                            await ctx.send(embed=item, view=Paginator(paginator, ctx.author.id))
                        else:
                            if py_codeblock:
                                replacement = item.description.replace("`", "\u200b`")
                                item.description = f'```py\n{replacement}\n```'
                            items.append(item)
                    else:
                        items.append(item)
            if str_type:
                kwargs[str_type] = items

        elif isinstance(arg, discord.ui.View):
            kwargs["view"] = arg

        else:
            content = _revert_virtual_var_value(str(arg).replace(ctx.bot.http.token, "TOKEN"))
            if len(content) > 1990:
                paginator = commands.Paginator(prefix="```py\n", suffix="\n```")
                for line in content.split("\n"):
                    paginator.add_line(line)
                await ctx.send(paginator.pages[0], view=Paginator(paginator, ctx.author.id))
            else:
                if py_codeblock:
                    content = content.replace("`", "\u200b`")
                    content = f"```py\n{content}\n```"
                kwargs["content"] = content
    if kwargs:
        return await ctx.send(**kwargs)


async def generate_ctx(ctx: commands.Context, author: discord.Member, channel: discord.TextChannel, **kwargs) -> commands.Context:
    """Create a custom context with changeable attributes.

    Parameters
    ----------
    ctx: :class:`commands.Context`
        The default context in which the command was invoked on.
    author: :class:`discord.Member`
        A new author that the generated context should have.
    channel: :class:`discord.TextChannel`
        A new text channel that the generated context should have.
    kwargs:
        Any other additional attributes that the generated context should have.

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


def _revert_virtual_var_value(string: str) -> str:
    # For security reasons, when using await send(), this gets automatically called
    for var_name, var_value in local_globals.items():
        string = string.replace(var_value, var_name)
    return string
