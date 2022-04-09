import re
import discord

from copy import copy
from discord.ext import commands

from dev.utils.startup import get_owner, settings


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
        elif ctx.author.id in owner_ids:
            return True
        raise commands.NotOwner("You either do not own this bot or are not listed in the override owner list.")
    return commands.check(owner)


def clean_code(content: str):
    if content.startswith("```") and content.endswith("```"):
        return "\n".join(content.split("\n")[1:-1])
    else:
        return content
