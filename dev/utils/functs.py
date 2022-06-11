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
    Optional,
    Union
)

import discord
import io
import json

from discord.ext import commands
from copy import copy

from dev.handlers import Paginator

from dev.utils.utils import local_globals


__all__ = (
    "all_commands",
    "flag_parser",
    "generate_ctx",
    "send",
    "table_creator"
)


def all_commands(command_list: set) -> List[Union[commands.Command, commands.Group]]:
    command_count = []
    for command in command_list:
        if isinstance(command, commands.Group):
            command_count.append(command)
            for cmd in all_commands(command.commands):
                command_count.append(cmd)
        else:
            command_count.append(command)
    return command_count


def flag_parser(string: str, delimiter: str) -> Union[Dict[str, str], str]:
    """Converts a string into a dictionary.

    Parameters
    ----------
    string: :class:`str`
        The string that should be converted.
    delimiter: :class:`str`
        The characters that separate keys and values.

    Examples
    --------
    .. codeblock:: python3
        >>> my_string = 'key=value abc=foo bar'
        >>> flag_parser(my_string, '=')
        {'key': 'value', 'abc': 'foo bar'}

    Returns
    -------
    dict
        The converted dictionary.
    """
    keys, values = [], []
    temp_string = ""
    searching_for_value = False
    for char in string:
        if char == delimiter:
            if searching_for_value:
                values.append(" ".join(temp_string.split()[:-1]))
                keys.append(temp_string.split()[-1])
                searching_for_value = False
                temp_string = ""
            else:
                keys.append(temp_string)
                searching_for_value = True
                temp_string = ""
            continue
        temp_string += char
    if temp_string:
        values.append(temp_string)
    for i in range(len(values)):
        try:
            values[i] = json.loads(values[i])
        except json.JSONDecodeError as error:
            return f"{error}."
    return dict(zip(keys, values))


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


async def send(ctx: commands.Context, *args: Union[Sequence[Union[discord.Embed, discord.File]], discord.Embed, discord.File, discord.ui.View, str], **options) -> Optional[discord.Message]:
    """Evaluates how to safely send a discord message.

    This replaces the bot's token with '[token]' and converts any values of variables back to their keys.

    Parameters
    ----------
    ctx: :class:`commands.Context`
        The context in which the command was invoked on. This is used to send the message and get the bot's token.
    args:
        Arguments that will be sent to :meth:`ctx.send`. These can be Embeds, Files, Views, or strings. Additionally,
        Embeds and Files can be inside a list, tuple or set to send multiple of these types.

    Returns
    -------
    discord.Message
        The message that was sent. This does not include Pagination messages.

    Raises
    ------
    TypeError
        A list, tuple or set contains more than one type, e.g: [discord.File, discord.File, discord.Embed].
    """
    use_codeblock: bool = options.get("codeblock")
    kwargs = {}
    for arg in args:
        if isinstance(arg, discord.Embed):
            arg = _embed_inspector(ctx.bot, arg)
            return_type = _check_length(arg, 6000)
            if isinstance(return_type, commands.Paginator):
                await ctx.send(embed=arg, view=Paginator(return_type, ctx.author.id))
            else:
                kwargs["embed"] = arg

        elif isinstance(arg, discord.File):
            string = _revert_virtual_var_value("".join(line.decode('utf-8') for line in arg.fp.readlines()).replace(ctx.bot.http.token, "[token]")).encode('utf-8')
            kwargs["file"] = discord.File(filename=f"{arg.filename}.txt" if "." not in arg.filename else arg.filename, fp=io.BytesIO(string))

        elif isinstance(arg, (list, set, tuple)):
            items = []
            str_type = ""
            inst_type = None
            for item in arg:
                if isinstance(item, discord.File):
                    if inst_type:
                        if not isinstance(item, inst_type):
                            raise TypeError(f"Found multiple types inside a {type(arg).__name__}. Expected {inst_type.__name__} but received {type(item).__name__}")
                    str_type = "files"
                    inst_type = discord.File
                    string = _revert_virtual_var_value("".join(line.decode('utf-8') for line in item.fp.readlines()).replace(ctx.bot.http.token, "[token]")).encode('utf-8')
                    items.append(discord.File(filename=f"{item.filename}.txt" if "." not in item.filename else item.filename, fp=io.BytesIO(string)))
                elif isinstance(item, discord.Embed):
                    if inst_type:
                        if not isinstance(item, inst_type):
                            raise TypeError(f"Found multiple types inside a {type(arg).__name__}. Expected {inst_type.__name__} but received {type(item).__name__}")
                    str_type = "embeds"
                    inst_type = discord.Embed
                    item = _embed_inspector(ctx.bot, item)
                    return_type = _check_length(item, 6000)
                    if isinstance(return_type, commands.Paginator):
                        await ctx.send(embed=item, view=Paginator(return_type, ctx.author.id))
                    else:
                        items.append(item)
            if str_type:
                kwargs[str_type] = items

        elif isinstance(arg, discord.ui.View):
            kwargs["view"] = arg

        else:
            content = _revert_virtual_var_value(str(arg)).replace(ctx.bot.http.token, "[token]")
            content = content if not use_codeblock else f"```py\n{content}\n```"
            return_type = _check_length(content)
            if isinstance(return_type, commands.Paginator):
                await ctx.send(content, view=Paginator(return_type, ctx.author.id))
            else:
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
    # noinspection PyProtectedMember
    alt_msg._update(kwargs)
    alt_msg.author = author
    alt_msg.channel = channel
    return await ctx.bot.get_context(alt_msg, cls=type(ctx))


def _embed_inspector(bot: commands.Bot, embed: discord.Embed) -> discord.Embed:
    if embed.title:
        embed.title = _revert_virtual_var_value(embed.title).replace(bot.http.token, "[token]")
    if embed.description:
        if embed.description.startswith("```") and embed.description.endswith("```"):
            embed.description = embed.description.split("\n")[0] + "\n" + _revert_virtual_var_value("\n".join(embed.description.split("\n")[1:-1])).replace(bot.http.token, "[token]").replace("``", "`\u200b`") + "```"
        else:
            embed.description = _revert_virtual_var_value(embed.description).replace(bot.http.token, "[token]")
    if embed.author:
        embed.author.name = _revert_virtual_var_value(embed.author.name).replace(bot.http.token, "[token]")
    if embed.footer:
        embed.footer.text = _revert_virtual_var_value(embed.footer.text).replace(bot.http.token, "[token]")
    if embed.fields:
        for field in embed.fields:
            field.name = _revert_virtual_var_value(field.name).replace(bot.http.token, "[token]")
            if field.value.startswith("```") and field.value.endswith("```"):
                field.value = field.value.split("\n")[0] + "\n" + _revert_virtual_var_value("\n".join(field.value.split("\n")[1:-1])).replace(bot.http.token, "[token]").replace("``", "`\u200b`") + "```"
            else:
                field.value = _revert_virtual_var_value(field.value).replace(bot.http.token, "[token]")
    return embed


def _check_length(content: Union[discord.Embed, str], max_length: int = 2000) -> Union[commands.Paginator, str]:
    if len(content) > max_length:
        prefix, suffix = "```py\n", "\n```"
        if isinstance(content, discord.Embed):
            if content.description.startswith("```") and content.description.endswith("```"):
                prefix = content.description.split("\n")[0] + "\n"
            paginator = commands.Paginator(prefix=prefix, suffix=suffix)
            for line in content.description.split("\n")[1:-1]:
                paginator.add_line(line.replace("``", "`\u200b`"))
            return paginator
        else:
            if content.startswith("```") and content.endswith("```"):
                prefix = content.split("\n")[0] + "\n"
            paginator = commands.Paginator(prefix=prefix, suffix=suffix)
            for line in content.split("\n")[1:-1]:
                paginator.add_line(line.replace("``", "`\u200b`"))
            return paginator
    return content


def _revert_virtual_var_value(string: str) -> str:
    # For security reasons, when using await send(), this gets automatically called
    for var_name, var_value in local_globals.items():
        string = string.replace(var_value, var_name)
    return string
