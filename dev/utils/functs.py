# -*- coding: utf-8 -*-

"""
dev.utils.functs
~~~~~~~~~~~~~~~

Basic functions used within the dev extension.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import io
import json
import math
from copy import copy
from typing import TYPE_CHECKING, Any, Optional, TypeVar

import discord
from discord.ext import commands
from discord.utils import MISSING

from dev.types import InteractionResponseType
from dev.pagination import Interface, Paginator

from dev.utils.baseclass import Root

if TYPE_CHECKING:
    from collections.abc import Sequence

    from discord.http import HTTPClient

    from dev import types


__all__ = (
    "all_commands",
    "flag_parser",
    "generate_ctx",
    "interaction_response",
    "send",
    "table_creator"
)

TypeT = TypeVar("TypeT", str, discord.Embed)


def all_commands(command_list: set[types.Command]) -> set[types.Command]:
    """Retrieve all commands that are currently available from a given set.

    Unlike :meth:`discord.ext.commands.Bot.commands`, group subcommands are also returned.

    Parameters
    ----------
    command_list: Set[types.Command]
        A set of commands, groups or both.

    Returns
    -------
    List[types.Command]
        The full list of all the commands that were found within `command_list`.
    """
    command_count = set()
    for command in command_list:
        if isinstance(command, commands.Group):
            command_count.add(command)
            for cmd in all_commands(command.commands):
                command_count.add(cmd)
        else:
            command_count.add(command)
    return command_count


def flag_parser(string: str, delimiter: str) -> dict[str, Any]:
    """Converts a string into a dictionary.

    This works similarly to :class:`discord.ext.commands.FlagConverter`, only that it can
    take an arbitrary number of flags and prefixes aren't supported.

    Examples
    --------
    .. codeblock:: python3
        >>> my_string = 'key=value abc=foo bar'
        >>> flag_parser(my_string, '=')
        {'key': 'value', 'abc': 'foo bar'}

    Parameters
    ----------
    string: :class:`str`
        The string that should be converted.
    delimiter: :class:`str`
        The character(s) that separate keys and values.

    Returns
    -------
    Dict[:class:`str`, Any]
        The parsed string dictionary.
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
        values[i] = json.loads(str(values[i]).lower() if values[i] is not None else 'null')
    return dict(zip(keys, values))


def table_creator(rows: list[list[Any]], labels: list[str]) -> str:
    table: list[dict[Any, list[Any]]] = []
    table_str = ""
    for label in labels:
        if label == labels[1]:
            largest = max([row[1] for row in rows], key=lambda x: len(x))
            if len(largest) < len(label):
                for row in rows:
                    first, second = (len(label) - len(row[1])) // 2, math.ceil((len(label) - len(row[1])) / 2)
                    row[1] = (" " * first) + row[1] + (" " * second)
            elif len(largest) > len(label):
                first, second = (len(largest) - len(label)) // 2, math.ceil((len(largest) - len(label)) / 2)
                label = (" " * first) + label + (" " * second)
                for row in rows:
                    first, second = (len(largest) - len(row[1])) // 2, round((len(largest) - len(row[1])) / 2)
                    row[1] = (" " * first) + row[1] + (" " * second)
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


async def send(ctx: commands.Context, *args: types.MessageContent, **options: Any) -> Optional[discord.Message]:
    """Evaluates how to safely send a Discord message.

    `content`, `embed`, `embeds`, `file`, `files` and `view` are all positional arguments instead of keywords.
    Everything else that is available in :meth:`commands.Context.send` remain as keyword arguments.

    This function replaces the token of the bot with '[token]' and converts any instances of a virtual variable's
    value back to its respective key.

    See Also
    --------
    :meth:`discord.ext.commands.Context.send`

    Parameters
    ----------
    ctx: :class:`commands.Context`
        The invocation context in which the command was invoked.
    args: MessageContent
        Arguments that will be passed to :meth:`commands.Context.send`.
        Embeds and files can be inside a list, tuple or set to send multiple of these types.
    options:
        Keyword arguments that will be passed to :meth:`commands.Context.send`.

    Returns
    -------
    Optional[:class:`discord.Message`]
        The message that was sent. This does not include pagination messages.

    Raises
    ------
    TypeError
        A list, tuple or set contains more than one type.
    """
    forced: bool = options.get("forced", False)
    kwargs = {}
    for arg in args:
        if isinstance(arg, discord.Embed):
            arg = _embed_inspector(ctx.bot.http, arg)
            return_type = _check_length(arg, 4096)
            if isinstance(return_type, Paginator):
                view = Interface(return_type, ctx.author.id)
                arg.description = view.display_page
                await ctx.send(embed=arg, view=view)
            else:
                kwargs["embed"] = arg

        elif isinstance(arg, discord.File):
            string = _revert_virtual_var_value(
                arg.fp.read().decode("utf-8").replace(ctx.bot.http.token, "[token]")
            ).encode("utf-8")
            kwargs["file"] = discord.File(filename=arg.filename, fp=io.BytesIO(string))

        elif isinstance(arg, (list, set, tuple)):
            items = []
            inst_type: Optional[type] = None
            for item in arg:
                if isinstance(item, discord.File):
                    if inst_type:
                        if not isinstance(item, inst_type):
                            raise TypeError(
                                f"Found multiple types inside a single {type(arg).__name__}. "
                                f"Expected {inst_type.__name__} but received {type(item).__name__}"
                            )
                    inst_type = discord.File
                    string = _revert_virtual_var_value(
                        item.fp.read().decode("utf-8").replace(ctx.bot.http.token, "[token]")
                    ).encode("utf-8")
                    items.append(discord.File(filename=item.filename, fp=io.BytesIO(string)))
                elif isinstance(item, discord.Embed):
                    if inst_type:
                        if not isinstance(item, inst_type):
                            raise TypeError(
                                f"Found multiple types inside a single {type(arg).__name__}. "
                                f"Expected {inst_type.__name__} but received {type(item).__name__}"
                            )
                    inst_type = discord.Embed
                    item = _embed_inspector(ctx.bot.http, item)
                    return_type = _check_length(item, 4096)
                    if isinstance(return_type, Paginator):
                        view = Interface(return_type, ctx.author.id)
                        item.description = view.display_page
                        await ctx.send(embed=item, view=view)
                    else:
                        items.append(item)
            if inst_type is not None:
                kwargs[inst_type.__name__.lower() + "s"] = items

        elif isinstance(arg, discord.ui.View):
            kwargs["view"] = arg

        else:
            content = _revert_virtual_var_value(str(arg)).replace(ctx.bot.http.token, "[token]")
            return_type = _check_length(content)
            if isinstance(return_type, Paginator):
                view = Interface(return_type, ctx.author.id)
                await ctx.send(view.display_page, view=view)
            else:
                kwargs["content"] = content
    if kwargs:
        kwargs.update(
            {
                "delete_after": options.get("delete_after"),
                "nonce": options.get("nonce"),
                "allowed_mentions": options.get("allowed_mentions", discord.AllowedMentions.none()),
                "reference": options.get("reference"),
                "mention_author": options.get("mention_author"),
                "stickers": options.get("stickers"),
                "tts": options.get("tts", False),
                "suppress_embeds": options.get("suppress_embeds", False)
             }
        )
        if ctx.message.id in Root.cached_messages and not forced:
            edit = {
                "content": kwargs.get("content"),
                "suppress": kwargs.get("suppress_embeds"),
                "delete_after": kwargs.get("delete_after"),
                "allowed_mentions": kwargs.get("allowed_mentions"),
                "view": kwargs.get("view")
            }
            if embed := kwargs.get("embed"):
                edit["embed"] = embed
            elif embeds := kwargs.get("embeds"):
                edit["embeds"] = embeds
            else:
                edit["embed"] = None
            if file := kwargs.get("file"):
                edit["attachments"] = [file]
            elif files := kwargs.get("files"):
                edit["attachments"] = files
            else:
                edit["attachments"] = []
            try:
                message = await Root.cached_messages[ctx.message.id].edit(**edit)
            except discord.HTTPException:
                message = await ctx.send(**kwargs)
        else:
            message = await ctx.send(**kwargs)
        Root.cached_messages[ctx.message.id] = message
        return message


async def interaction_response(
        interaction: discord.Interaction,
        response_type: InteractionResponseType,
        *args: Sequence[
                   discord.Embed | discord.File
               ] | discord.Embed | discord.File | discord.ui.View | discord.ui.Modal | str,
        **options: Any
) -> None:
    """Evaluates how to safely respond to a Discord interaction.

    `content`, `embed`, `embeds`, `file`, `files`, `modal` and `view` can all be optionally passed as positional
    arguments instead of keywords.
    Everything else that is available in :meth:`discord.InteractionResponse.send_message` and
    :meth:`discord.InteractionResponse.edit_message` remain as keyword arguments.

    This replaces the token of the bot with '[token]' and converts any instances of a virtual variable's value back to
    its respective key.

    If a modal is passed to this function, and `response_type` is set to `InteractionResponseType.MODAL`, no other
    arguments should be passed as this will raise a TypeError.

    See Also
    --------
    :meth:`discord.InteractionResponse.send_message`, :meth:`discord.InteractionResponse.edit_message`

    Parameters
    ----------
    interaction: :class:`discord.Interaction`
        The interaction that should be responded to.
    response_type: :class:`InteractionResponseType`
        The type of response that will be used to respond to the interaction. :meth:`discord.InteractionResponse.defer`
        isn't included.
    args: Union[
        Sequence[Union[:class:`discord.Embed`, :class:`discord.File`]],
        :class:`discord.Embed`,
        :class:`discord.File`,
        :class:`discord.ui.View`,
        :class:`discord.ui.Modal`,
        :class:`str`
    ]
        Arguments that will be passed to :meth:`discord.InteractionResponse.send_message` or
        :meth:`discord.InteractionResponse.edit_message`.
        Embeds and files can be inside a list, tuple or set to send multiple of these types.
    options:
        Keyword arguments that will be passed to :meth:`discord.InteractionResponse.send_message` or
        :meth:`discord.InteractionResponse.edit_message`.

    Raises
    ------
    TypeError
        Multiple arguments were passed when `response_type` was selected to `MODAL`.
        A list, tuple or set contains more than one type.
    """
    token = interaction.client.http.token
    assert token is not None
    if response_type is InteractionResponseType.SEND:
        method = interaction.response.send_message
    elif response_type is InteractionResponseType.EDIT:
        method = interaction.response.edit_message
    elif response_type is InteractionResponseType.MODAL:
        if tuple(map(type, args)) != (discord.ui.Modal,):
            raise TypeError("discord.ui.Modal should be the only argument passed to the function")
        modal: discord.ui.Modal = args[0]  # type: ignore
        #  just making sure
        modal.title.replace(token, "[token]")
        for children in modal.children:
            children.label.replace(token, "[token]")  # type: ignore
            if children.default is not None:  # type: ignore
                children.default.replace(token, "[token]")  # type: ignore
            if children.placeholder is not None:  # type: ignore
                children.placeholder.replace(token, "[token]")  # type:ignore
        return await interaction.response.send_modal(modal)
    else:
        raise TypeError("Invalid response type")
    kwargs = _check_kwargs(options)
    paginators: list[dict[str, Any]] = []
    for arg in args:
        if isinstance(arg, discord.Embed):
            arg = _embed_inspector(interaction.client.http, arg)
            return_type = _check_length(arg, 4096)
            if isinstance(return_type, Paginator):
                view = Interface(return_type, interaction.user.id)
                arg.description = view.display_page
                paginators.append(({"embed": arg, "view": view}))
            else:
                kwargs["embed"] = arg

        elif isinstance(arg, discord.File):
            string = _revert_virtual_var_value(
                arg.fp.read().decode("utf-8").replace(token, "[token]")
            ).encode("utf-8")
            kwargs["file"] = discord.File(filename=arg.filename, fp=io.BytesIO(string))

        elif isinstance(arg, (list, set, tuple)):
            items = []
            inst_type: Optional[type] = None
            for item in arg:
                if isinstance(item, discord.File):
                    if inst_type:
                        if not isinstance(item, inst_type):
                            raise TypeError(
                                f"Found multiple types inside a single {type(arg).__name__}. "
                                f"Expected {inst_type.__name__} but received {type(item).__name__}"
                            )
                    inst_type = discord.File
                    string = _revert_virtual_var_value(
                        item.fp.read().decode("utf-8").replace(token, "[token]")
                    ).encode("utf-8")
                    items.append(discord.File(filename=item.filename, fp=io.BytesIO(string)))
                elif isinstance(item, discord.Embed):
                    if inst_type:
                        if not isinstance(item, inst_type):
                            raise TypeError(
                                f"Found multiple types inside a {type(arg).__name__}. "
                                f"Expected {inst_type.__name__} but received {type(item).__name__}"
                            )
                    inst_type = discord.Embed
                    item = _embed_inspector(interaction.client.http, item)
                    return_type = _check_length(item, 4096)
                    if isinstance(return_type, Paginator):
                        view = Interface(return_type, interaction.user.id)
                        item.description = view.display_page
                        paginators.append(({"embed": item, "view": view}))
                    else:
                        items.append(item)
            if inst_type is not None:
                kwargs[inst_type.__name__.lower() + "s"] = items

        elif isinstance(arg, discord.ui.View):
            kwargs["view"] = arg

        else:
            content = _revert_virtual_var_value(str(arg)).replace(token, "[token]")
            return_type = _check_length(content)
            if isinstance(return_type, Paginator):
                view = Interface(return_type, interaction.user.id)
                paginators.append(({"content": view.display_page, "view": view}))
            else:
                kwargs["content"] = content
    responded = False
    if kwargs:
        kwargs.update(allowed_mentions=options.get("allowed_mentions", discord.AllowedMentions.none()))
        if response_type is InteractionResponseType.SEND:
            kwargs.update(
                ephemeral=options.get("ephemeral", False),
                tts=options.get("tts", False),
                suppress_embeds=options.get("suppress_embeds", False)
            )
        await method(**kwargs)
        responded = True
    if paginators:
        if not responded:
            await interaction.response.send_message(**paginators[0])
            del paginators[0]
        for pag in paginators:
            await interaction.followup.send(**pag)


async def generate_ctx(ctx: commands.Context, **kwargs: Any) -> commands.Context:
    """Create a custom context with changeable attributes.

    Parameters
    ----------
    ctx: :class:`commands.Context`
        The invocation context in which the command was invoked.
    kwargs:
        Any attributes that the generated context should have.

    Returns
    -------
    :class:`commands.Context`
        A newly created context with the given attributes.
    """
    alt_msg: discord.Message = copy(ctx.message)
    # noinspection PyProtectedMember
    alt_msg._update(kwargs)  # type: ignore
    return await ctx.bot.get_context(alt_msg, cls=type(ctx))


def _embed_inspector(http: HTTPClient, embed: discord.Embed) -> discord.Embed:
    assert http.token is not None
    if embed.title:
        embed.title = _revert_virtual_var_value(embed.title).replace(http.token, "[token]")
    if embed.description:
        if embed.description.startswith("```") and embed.description.endswith("```"):
            embed.description = embed.description.split("\n")[0] + "\n" + _revert_virtual_var_value(
                "\n".join(embed.description.split("\n")[1:-1])
            ).replace(http.token, "[token]").replace("``", "`\u200b`") + "```"
        else:
            embed.description = _revert_virtual_var_value(embed.description).replace(http.token, "[token]")
    if embed.author.name is not None:
        embed.author.name = _revert_virtual_var_value(embed.author.name).replace(http.token, "[token]")
    if embed.footer.text is not None:
        embed.footer.text = _revert_virtual_var_value(embed.footer.text).replace(http.token, "[token]")
    if embed.fields:
        for field in embed.fields:
            assert field.name is not None and field.value is not None
            field.name = _revert_virtual_var_value(field.name).replace(http.token, "[token]")
            if field.value.startswith("```") and field.value.endswith("```"):
                field.value = field.value.split("\n")[0] + "\n" + _revert_virtual_var_value(  # type: ignore
                    "\n".join(field.value.split("\n")[1:-1])
                ).replace(http.token, "[token]").replace("``", "`\u200b`") + "```"
            else:
                field.value = _revert_virtual_var_value(field.value).replace(http.token, "[token]")
    return embed


def _check_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    _kwargs = {
        "content": kwargs.pop("content", MISSING),
        "embed": kwargs.get("embed", MISSING),
        "embeds": kwargs.get("embeds", MISSING),
        "file": kwargs.get("file", MISSING),
        "files": kwargs.get("files", MISSING),
        "view": kwargs.get("view", MISSING)
    }
    return {k: v for k, v in _kwargs.items() if v is not MISSING}


def _check_length(content: TypeT, max_length: int = 2000) -> Paginator | TypeT:
    if len(content) > max_length:
        highlight_lang = ""
        if isinstance(content, discord.Embed):
            if content.description is None:
                raise TypeError(
                    "Support for pagination in fields other than the description are not supported for embeds"
                )
            string = content.description
            if string.startswith("```") and string.endswith("```"):
                highlight_lang = string.split("\n")[0].removeprefix("```")
                string = "\n".join(content.description.split("\n")[1:-1])
            paginator = Paginator(content, prefix=f"```{highlight_lang}", max_size=max_length)
            for line in string.split("\n"):
                paginator.add_line(line.replace("``", "`\u200b`"))
            return paginator
        else:
            string = content
            if content.startswith("```") and content.endswith("```"):
                highlight_lang = content.split("\n")[0].removeprefix("```")
                string = "\n".join(content.split("\n")[1:-1])
            paginator = Paginator(content, prefix=f"```{highlight_lang}", max_size=max_length)
            for line in string.split("\n"):
                paginator.add_line(line.replace("``", "`\u200b`"))
            return paginator
    return content


def _revert_virtual_var_value(string: str) -> str:
    # For security reasons, when using await send(), this gets automatically called
    for name, value in Root.scope.globals.items():
        string = string.replace(value, name)
    for name, value in Root.scope.locals.items():
        string = string.replace(value, name)
    return string
