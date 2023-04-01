# -*- coding: utf-8 -*-

"""
dev.utils.functs
~~~~~~~~~~~~~~~~

Basic functions used within the dev extension.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import io
import json
from collections.abc import Iterable
from copy import copy
from typing import TYPE_CHECKING, Any, Literal, TypeVar, overload

import discord
from discord.ext import commands
from discord.utils import MISSING

from dev import root
from dev.pagination import Interface, Paginator
from dev.scope import Settings

if TYPE_CHECKING:
    from collections.abc import Sequence

    from dev import types

T = TypeVar("T")

__all__ = ("flag_parser", "generate_ctx", "generate_table", "interaction_response", "send")


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
    keys: list[str] = []
    values: list[str] = []
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
    for idx, value in enumerate(values):
        values[idx] = json.loads(str(value).lower())
    return dict(zip(keys, values))


def generate_table(**label_rows: list[str]) -> str:
    table: dict[str, list[str]] = {}

    def fmt(s: str, pad: int) -> str:
        if len(s) > 13:
            return s[:10] + "..."
        return f"{{0:<{pad}}}".format(s)

    longest = len(max(label_rows.values(), key=len))

    for idx, row in enumerate(label_rows.values()):
        label = tuple(label_rows)[idx]
        largest = max((*row, label), key=len)
        padding = len(largest)
        extra = max(longest - len(row), 0)
        if idx == len(label_rows) - 1:
            table[label] = row + [""] * extra
        else:
            table[fmt(label, padding)] = [fmt(r, padding) for r in row] + [""] * extra
    ordered: list[list[str]] = []
    for idx in range(longest):
        row_values: list[str] = []
        for row_idx in range(len(table.values())):
            row_values.append(tuple(table.values())[row_idx][idx])
        ordered.append(row_values)
    splitter = "+".join("-" * (len(lab) + (1 if idx == 0 else 2)) for idx, lab in enumerate(table))
    rendered: list[str] = [" | ".join(table), splitter.replace("-", "=")]
    rendered.extend(" | ".join(r) + "\n" + splitter for r in ordered)
    return "\n".join(rendered)


@overload
async def send(
    ctx: commands.Context[types.Bot], *args: types.MessageContent, paginator: Paginator | Literal[None], **options: Any
) -> tuple[discord.Message, Paginator | None]:
    ...


@overload
async def send(  # type: ignore
    ctx: commands.Context[types.Bot], *args: types.MessageContent, **options: Any
) -> discord.Message:
    ...


async def send(  # type: ignore
    ctx: commands.Context[types.Bot], *args: Any, paginator: Any = MISSING, **options: Any
) -> Any:
    """Evaluates how to safely send a Discord message.

    `content`, `embed`, `embeds`, `file`, `files`, `stickers` and `view` are all positional
    arguments.
    Everything else that is available in :meth:`commands.Context.send` remain as keyword arguments.

    This replaces the token of the bot with '[token]' and converts any instances of a virtual
    variable's value back to its respective key.

    See Also
    --------
    :meth:`discord.ext.commands.Context.send`

    Parameters
    ----------
    ctx: :class:`commands.Context`
        The invocation context in which the command was invoked.
    args: MessageContent
        Arguments that will be passed to :meth:`commands.Context.send`.
        Embeds and files can be inside a container class to send multiple of these types.
    options:
        Keyword arguments that will be passed to :meth:`commands.Context.send`.

    Returns
    -------
    Tuple[:class:`discord.Message`, Optional[:class:`Paginator`]]
        The message that was sent and the paginator if `forced_pagination` was set to `False`.

    Raises
    ------
    IndexError
        `content` exceeded the 2000-character limit, and `view` did not permit pagination to work
        due to the amount of components it included.
    """
    replace_path_to_file: bool = options.pop("path_to_file", True)
    forced: bool = options.pop("forced", False)
    forced_pagination: bool = options.pop("forced_pagination", True)

    ret_paginator: Paginator | None = None
    last_message: discord.Message | None = None

    token = ctx.bot.http.token
    assert token is not None

    kwargs: dict[str, Any] = {}
    pag_view: Interface | None = None
    iterable_items: list[str] = []
    for item in args:
        if isinstance(item, discord.File):
            _try_add("files", _check_file(item, token, replace_path_to_file), kwargs)
        elif isinstance(item, discord.Embed):
            _try_add("embeds", _check_embed(item, token, replace_path_to_file), kwargs)
        elif isinstance(item, (discord.GuildSticker, discord.StickerItem)):
            _try_add("stickers", item, kwargs)
        elif isinstance(item, discord.ui.View):
            kwargs["view"] = item
        elif isinstance(item, Iterable) and not isinstance(item, str):
            for i in item:  # type: ignore
                if isinstance(i, discord.File):
                    _try_add("files", _check_file(i, token, replace_path_to_file), kwargs)
                elif isinstance(i, discord.Embed):
                    _try_add("embeds", _check_embed(i, token, replace_path_to_file), kwargs)
                elif isinstance(i, (discord.GuildSticker, discord.StickerItem)):
                    _try_add("stickers", i, kwargs)
                else:
                    iterable_items.append(_replace(repr(i), token, path=replace_path_to_file))  # type: ignore
        else:
            content = _replace(_revert_virtual_var_value(str(item)), token, path=replace_path_to_file)
            if iterable_items:
                content = "\n".join(iterable_items) + "\n" + content
                iterable_items.clear()
            if paginator is not MISSING and paginator is not None:
                for line in content.split("\n"):
                    paginator.add_line(line)
                pag_view = Interface(paginator, ctx.author.id)
            else:
                return_type = _check_length(content)
                if isinstance(return_type, Paginator):
                    pag_view = Interface(return_type, ctx.author.id)
                    if forced_pagination:
                        last_message = await ctx.send(pag_view.display_page, view=pag_view)
                    else:
                        ret_paginator = return_type
                else:
                    lang, content = _get_highlight_lang(content)
                    if lang is not None:
                        content = f"```{lang}\n" + content.replace("``", "`\u200b`") + "```"
                    kwargs["content"] = content
    kwargs.update(_check_kwargs(options))
    if not kwargs and last_message is not None:
        return last_message
    view: discord.ui.View | None = kwargs.get("view")
    if not forced_pagination and pag_view is not None:
        if view is not None:
            if len(view.children) > 15:
                raise IndexError("Content exceeds character limit, but view attached does not permit pagination")
            for idx, child in enumerate(view.children):
                child.row = idx // 5 + 2  # move after 'Quit' and pagination buttons
                pag_view.add_item(child)
        kwargs["content"] = pag_view.display_page
    cached = discord.utils.get(ctx.bot._connection._messages or [], id=ctx.message.id)
    if cached is not None and not forced:
        edit: dict[str, Any] = {
            "content": kwargs.get("content", None),
            "embeds": kwargs.get("embeds", []),
            "attachments": kwargs.get("files", []),
            "suppress": kwargs.get("suppress_embeds", False),
            "delete_after": kwargs.get("delete_after"),
            "allowed_mentions": kwargs.get("allowed_mentions", MISSING),
            "view": kwargs.get("view", None),
        }
        if pag_view is not None and not forced_pagination:
            edit["view"] = pag_view
        try:
            message = await cached.edit(**edit)
        except discord.HTTPException:
            message = await ctx.send(**kwargs)
    else:
        message = await ctx.send(**kwargs)
    if paginator is not MISSING:
        return message, ret_paginator
    return message


@overload
async def interaction_response(
    interaction: discord.Interaction,
    response_type: discord.InteractionResponseType,
    *args: str | discord.Embed | discord.File | discord.ui.View | discord.ui.Modal | Sequence[Any],
    paginator: Paginator | Literal[None],
    **options: Any,
) -> Paginator | None:
    ...


@overload
async def interaction_response(  # type: ignore
    interaction: discord.Interaction,
    response_type: discord.InteractionResponseType,
    *args: str | discord.Embed | discord.File | discord.ui.View | discord.ui.Modal | Sequence[Any],
    **options: Any,
) -> None:
    ...


async def interaction_response(  # type: ignore
    interaction: Any, response_type: Any, *args: Any, paginator: Any = MISSING, **options: Any
) -> Any:
    """Evaluates how to safely respond to a Discord interaction.

    `content`, `embed`, `embeds`, `file`, `files`, `modal` and `view` can all be optionally
    passed as positional arguments instead of keywords.
    Everything else that is available in :meth:`discord.InteractionResponse.send_message` and
    :meth:`discord.InteractionResponse.edit_message` remain as keyword arguments.

    This replaces the token of the bot with '[token]' and converts any instances of a virtual
    variable's value back to its respective key.

    If the response type is set to :class:`InteractionResponseType.MODAL`, then the first argument
    passed to `args` should be the modal that should be sent.

    See Also
    --------
    :meth:`discord.InteractionResponse.send_message`,
    :meth:`discord.InteractionResponse.edit_message`

    Parameters
    ----------
    interaction: :class:`discord.Interaction`
        The interaction that should be responded to.
    response_type: :enum:`InteractionResponseType`
        The type of response that will be used to respond to the interaction.
        :meth:`discord.InteractionResponse.defer` isn't included.
    args: Union[
        Sequence[Any],
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

    Returns
    -------
    Optional[:class:`Paginator`]
        The paginator that is being used in the first message if `forced_paginator` was
        set to `False` and the function decided to enable pagination for the response.

    Raises
    ------
    ValueError
        `response_type` was set to `MODAL`, but the first argument of `args` was not the modal.
    TypeError
        An invalid response type was passed.
    IndexError
        `content` exceeded the 2000-character limit, and `view` did not permit pagination to work
        due to the amount of components it included.
    """
    if response_type is discord.InteractionResponseType.channel_message:
        method = interaction.response.send_message
    elif response_type is discord.InteractionResponseType.message_update:
        method = interaction.response.edit_message
    elif response_type is discord.InteractionResponseType.modal:
        if not isinstance(args[0], discord.ui.Modal):
            raise ValueError(f"Expected type {discord.ui.Modal} at index 0 but received {type(args[0])} instead")
        return await interaction.response.send_modal(args[0])
    else:
        raise TypeError("Invalid response type")

    ret_paginator: Paginator | None = None
    token = interaction.client.http.token
    assert token is not None

    replace_path_to_file: bool = options.pop("path_to_file", True)
    forced_pagination: bool = options.pop("forced_paginator", True)
    paginators: list[Interface] = []

    kwargs: dict[str, Any] = {}
    pag_view: Interface | None = None
    iterable_items: list[str] = []
    for item in args:
        if isinstance(item, discord.File):
            _try_add("files", _check_file(item, token, replace_path_to_file), kwargs)
        elif isinstance(item, discord.Embed):
            _try_add("embeds", _check_embed(item, token, replace_path_to_file), kwargs)
        elif isinstance(item, discord.ui.View):
            kwargs["view"] = item
        elif isinstance(item, Iterable) and not isinstance(item, str):
            for i in item:  # type: ignore
                if isinstance(i, discord.File):
                    _try_add("files", _check_file(i, token, replace_path_to_file), kwargs)
                elif isinstance(i, discord.Embed):
                    _try_add("embeds", _check_embed(i, token, replace_path_to_file), kwargs)
                else:
                    iterable_items.append(_replace(repr(i), token, path=replace_path_to_file))  # type: ignore
        else:
            content = _replace(_revert_virtual_var_value(str(item)), token, path=replace_path_to_file)
            lang, content = _get_highlight_lang(content)
            if lang is not None:
                content = f"```{lang}\n" + content.replace("``", "`\u200b`") + "```"
            if iterable_items:
                content = "\n".join(iterable_items) + "\n" + content
                iterable_items.clear()
            if paginator is not MISSING and paginator is not None:
                for line in content.splitlines():
                    paginator.add_line(line)
                pag_view = Interface(paginator, interaction.user.id)
            else:
                return_type = _check_length(content)
                if isinstance(return_type, Paginator):
                    pag_view = Interface(return_type, interaction.user.id)
                    if forced_pagination:
                        paginators.append(pag_view)
                    else:
                        ret_paginator = return_type
                else:
                    kwargs["content"] = content

    kwargs = _check_kwargs(kwargs)
    view: discord.ui.View | None = kwargs.get("view")
    if view is not None and len(view.children) <= 15 and not forced_pagination and pag_view is not None:
        child: discord.ui.Item[discord.ui.View]
        for idx, child in enumerate(view.children):
            child.row = idx // 5 + 2  # move after 'Quit' and pagination buttons
            pag_view.add_item(child)
    elif view is not None and len(view.children) < 15 and not forced_pagination and pag_view is not None:
        raise IndexError("Content exceeds character limit, but view attached does not permit pagination")

    kwargs.update(allowed_mentions=options.get("allowed_mentions", discord.AllowedMentions.none()))
    if response_type is discord.InteractionResponseType.channel_message:
        kwargs.update(
            ephemeral=options.get("ephemeral", False),
            tts=options.get("tts", False),
            suppress_embeds=options.get("suppress_embeds", False),
            delete_after=options.get("delete_after"),
        )
    await method(**kwargs)
    for pag in paginators:
        await interaction.followup.send(pag.display_page, view=pag)
    if paginator is not MISSING:
        return ret_paginator


async def generate_ctx(ctx: commands.Context[types.Bot], **kwargs: Any) -> commands.Context[types.Bot]:
    """Create a custom context with changeable attributes.

    Parameters
    ----------
    ctx: :class:`commands.Context`
        The invocation context in which the command was invoked.
    kwargs:
        Any attributes that the generated context should have.

    Notes
    -----
    When specifying a new guild, it may not always get updated. This is mainly controlled
    by the message's text channel.
    There might be a few other really specific cases in which it may not get updated.

    Returns
    -------
    :class:`commands.Context`
        A newly created context with the given attributes.
    """
    author = kwargs.pop("author", ctx.author)
    channel = kwargs.pop("channel", ctx.channel)
    guild = kwargs.pop("guild", ctx.guild)

    message: discord.Message = copy(ctx.message)
    message._update(kwargs)  # type: ignore
    message.author = author or message.author
    message.channel = channel or message.channel
    message.guild = guild or message.guild

    return await ctx.bot.get_context(message, cls=type(ctx))


def _get_highlight_lang(content: str) -> tuple[str | None, str]:
    if content.startswith("```") and content.endswith("```"):
        lines = content.split("\n")
        highlight = lines[0][3:]
        if lines[-1] == "```":
            return highlight, "\n".join(lines[1:-1])
        return highlight, "\n".join(lines[1:])[:-3]
    return None, content


def _check_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    _kwargs = {
        "content": kwargs.pop("content", MISSING),
        "stickers": kwargs.pop("stickers", MISSING),
        "embeds": kwargs.get("embeds", MISSING),
        "files": kwargs.get("files", MISSING),
        "view": kwargs.get("view", MISSING),
    }
    return {k: v for k, v in _kwargs.items() if v is not MISSING}


def _try_add(key: str, value: T, dictionary: dict[str, list[T]]) -> None:
    try:
        dictionary[key].append(value)
    except KeyError:
        dictionary[key] = [value]


def _check_file(file: discord.File, token: str, /, replace_path: bool) -> discord.File:
    try:
        string = _revert_virtual_var_value(_replace(file.fp.read().decode("utf-8"), token, path=replace_path)).encode(
            "utf-8"
        )
    except UnicodeDecodeError:
        return file
    return discord.File(io.BytesIO(string), file.filename, spoiler=file.spoiler, description=file.description)


def _check_embed(embed: discord.Embed, token: str, /, replace_path: bool) -> discord.Embed:
    if title := embed.title:
        embed.title = _replace(title, token, path=replace_path)
    if description := embed.description:
        embed.description = _replace(description, token, path=replace_path)
    if footer := embed.footer.text:
        embed.footer.text = _replace(footer, token, path=replace_path)
    for field in embed.fields:
        assert field.name is not None and field.value is not None
        field.name = _replace(field.name, token, path=replace_path)
        field.value = _replace(field.value, token, path=replace_path)
    return embed


def _replace(string: str, token: str, /, *, path: bool) -> str:
    string = string.replace(token, "[token]")
    if path:
        string = string.replace(Settings.PATH_TO_FILE, "~")
    return string


def _check_length(content: str) -> Paginator | str:
    if len(content) > 2000:
        highlight_lang = ""
        string = content
        if content.startswith("```") and content.endswith("```"):
            highlight_lang = content.split("\n")[0][3:]
            string = "\n".join(content.split("\n")[1:])[:-3]
        paginator = Paginator(prefix=f"```{highlight_lang}")
        for line in string.split("\n"):
            paginator.add_line(line.replace("``", "`\u200b`"))
        return paginator
    return content


def _revert_virtual_var_value(string: str) -> str:
    for (name, value) in root.Plugin.scope.items():
        string = string.replace(value, name)
    return string
