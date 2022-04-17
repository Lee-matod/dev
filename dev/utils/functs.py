import io
import re

import discord

from copy import copy
from typing import TextIO
from discord.ext import commands

from dev.utils.baseclass import Paginator
from dev.utils.utils import local_globals
from dev.utils.startup import get_owner, settings


async def send(ctx: commands.Context, content=None, *, is_py_bt: bool = False, **options) -> discord.Message:
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
    alt_msg: discord.Message = copy(ctx.message)
    alt_msg._update(kwargs)
    alt_msg.author = author
    alt_msg.channel = channel
    return await ctx.bot.get_context(alt_msg, cls=type(ctx))


def convert_kwargs_format(formatter: str):
    format_style = re.compile(r"%\((\w+)\)s")
    f = re.finditer(format_style, formatter)
    re_format = []
    compiler = ""
    for i in f:
        if i:
            re_format.append(i.group(1))
    for i in re_format:
        if i == "key":
            compiler += r"\w+?"
        elif i == "sep":
            compiler += rf"{settings['kwargs']['separator']}"
        elif i == "word":
            compiler += r".*"
    return compiler


def is_owner():
    def owner(ctx: commands.Context):
        owner_ids = get_owner()
        if settings["owners"]:
            if ctx.author.id in settings["owners"]:
                return True
            raise commands.NotOwner("You either do not own this bot or are not listed in the override owner list.")
        elif ctx.author.id in owner_ids:
            return True
        raise commands.NotOwner("You either do not own this bot or are not listed in the override owner list.")
    return commands.check(owner)


def clean_code(content: str):
    if content.startswith("```") and content.endswith("```"):
        return "\n".join(content.split("\n")[1:-1])
    else:
        return content
