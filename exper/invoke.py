import discord
import re
import contextlib
import textwrap
import io
import shlex

from discord.ext import commands
from typing import Optional
from copy import copy

from dev.utils.functs import is_owner
from dev.utils.settings import settings
from dev.utils.baseclass import CContext, commands_


class ExecuteFlags(commands.FlagConverter):
    command_: Optional[str] = commands.flag(name="command", default=None)
    kwargs_: Optional[str] = commands.flag(name="kwargs", default={})
    args_: Optional[str] = commands.flag(name="args", default="")
    as_: Optional[discord.Member] = commands.flag(name="as", default=None)
    at_: Optional[discord.TextChannel] = commands.flag(name="at", default=None)
    say_: Optional[str] = commands.flag(name="say", default=None)
    dm_: Optional[discord.Member] = commands.flag(name="dm", default=None)


class ReinvokeFlags(commands.FlagConverter):
    is_command_: Optional[bool] = commands.flag(name="is_command", default=True)
    jump_url_: Optional[bool] = commands.flag(name="jump_url", default=False)
    skip_messages_: Optional[int] = commands.flag(name="skip_messages", default=0)
    history_limit_: Optional[int] = commands.flag(name="history_limit", default=100)
    has_: Optional[str] = commands.flag(name="has", default=None)
    startswith_: Optional[str] = commands.flag(name="startswith", default=None)
    endswith_: Optional[str] = commands.flag(name="endswith", default=None)
    author_: Optional[discord.Member] = commands.flag(name="author", default=None)


class RootInvoke(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands_.command(name="execute", aliases=["exec"], parent="dev")
    @is_owner()
    async def root_execute(ctx: commands.Context, *, flags: ExecuteFlags = commands.Option(description="Arguments that will be taken into consideration.")):
        """
        Execute a command with changeable given arguments and attributes. Customization is done via flags.
        **Flag arguments:**
        `command`: _str_ = The command to be executed. Defaults to _None_.
        `kwargs`: _str_ = Key-word arguments that should be passed to `command`. Defaults to an empty _dict_.
        `args`: _str_ = Arguments that should be passed to `command`. Defaults to an empty _str_.
        `as`: _discord.Member_ = Execute `command` where _ctx.author_ is the given _discord.Member_. Defaults to _None_.
        `at`: _discord.TextChannel_ = Execute`command` where _ctx.channel_ is the given _discord.TextChannel_. Defaults to _None_.
        `say`: _str_ = Make the bot send a string of characters. This will not be executed if `command` is a given flag. Defaults to _None_.
        `dm`: _discord.Member_ = Whether `say` should be a Direct Message to the given _discord.Member_. Defaults None.
        """
        embed_pattern = re.compile(r"discord\.Embed\(title=.*?\)((\.)?(add_field|set_footer|set_author)?\(?.*\)?)*")
        flags.args_ = shlex.split(flags.args_)
        new_ctx = await ctx.bot.get_context(ctx.message, cls=CContext)
        new_ctx.set_properties(flags.as_ or ctx.author, flags.at_ or ctx.channel)
        kwargs_dict = {}

        if flags.kwargs_:
            kwargs = shlex.split(flags.kwargs_)
            compiler = convert_kwargs_format(settings["kwargs"]["format"].strip())
            kwargs_pattern = re.compile(rf"{compiler}")
            for kw in kwargs:
                match = re.finditer(string=kw, pattern=kwargs_pattern)
                if match:
                    for m in match:
                        key, word = m.group().split(settings['kwargs']['separator'], 1)
                        kwargs_dict[key] = word

        elif flags.command_:
            try:
                command: commands.Command = ctx.bot.get_command(flags.command_)
                if command is None:
                    return await ctx.send(f"Command `{flags.command_}` is not found.")
                return await command.__call__(new_ctx, *flags.args_, **kwargs_dict)

            except Exception as e:
                return await ctx.send(embed=discord.Embed(title=e.__class__.__name__, description=f"```py\n{e}\n```", color=discord.Color.red()))

        elif flags.say_:
            matches = re.finditer(string=flags.say_, pattern=embed_pattern)
            say_say = flags.say_
            embeds_say = []
            kwargs = {}
            local_vars = {"ctx": new_ctx, "discord": discord}
            if matches:
                for match in matches:
                    if match.group().count("(") != match.group().count(")"):
                        amount = r".*?\)" * abs(match.group().count("(") - match.group().count(")"))
                        say_say, embeds_say = await re_iter(flags, local_vars, say_say, embeds_say, string=flags.say_, pattern=re.compile(r"discord\.Embed\(title=.*?\)" + amount + r"((\.)?(add_field|set_footer|set_author)?\(?.*\)?)*"))
                        continue
                    say_say, embeds_say = await re_iter(flags, local_vars, say_say, embeds_say, match=match)
            kwargs["content"] = say_say
            kwargs["embeds"] = embeds_say
            if flags.dm_:
                await flags.dm_.send(**kwargs)
                return await ctx.message.add_reaction("☑")
            return await new_ctx.send(**kwargs)

    @commands_.command(name="reinvoke", parent="dev")
    @is_owner()
    async def root_reinvoke(ctx: commands.Context, *, flags: ReinvokeFlags = commands.Option(description="Arguments that will be taken into consideration.")):
        """
        Reinvoke the last command that was executed or fetch a message by either ctx.author or a given user. Customization is done via flags.
        **Flag arguments:**
        `is_command`: _bool_ = Whether the bot should look for a command or a message. Defaults to _True_.
        `jump_url`: _bool_ = Whether the bot should send the url link to the message. Defaults to _False_.
        `skip_messages`: _int_ = How many messages the bot should skip before it starts searching. Defaults to 0.
        `history_limit`: _int_ = How many messages the bot will look through. Defaults to 100.
        `has`: _str_ = Check if the message has a specific sequence of characters. Defaults to _None_.
        `startswith`: _str_ = Check if the message startswith specific characters. Defaults to _None_.
        `endswith`: _str_ = Check if the message endswith specific characters. Defaults to _None_.
        `author`: _discord.Member_ = Who the author of the message should be. Defaults to _ctx.author_.
        """
        flags.author_ = flags.author_ or ctx.author

        messages = await ctx.channel.history(limit=flags.history_limit_).flatten()
        count = 0
        for message in messages:
            if message.author.id == flags.author_.id:
                if message.content.startswith(f"{ctx.prefix}dev reinvoke") and flags.is_command_:
                    flags.skip_messages_ += 1
                    count += 1
                    continue
                if count == flags.skip_messages_:
                    check = flag_checks(message, flags)
                    if check:
                        if flags.jump_url_:
                            await ctx.send(embed=discord.Embed(title="Message URL", url=message.jump_url))

                        if flags.is_command_ and message.content.startswith(ctx.prefix):
                            alt_ctx: commands.Context = await generate_ctx(ctx, ctx.author, ctx.channel, content=message.content)
                            return await alt_ctx.command.reinvoke(alt_ctx)

                        if not flags.is_command_ and not message.content.startswith(ctx.prefix):
                            return await ctx.send(
                                embed=discord.Embed(title=f"{flags.author_} said:", description=message.content, color=discord.Color.blurple()))

                        if not flags.is_command_ and message.content.startswith(ctx.prefix):
                            flags.skip_messages_ += 1
                            count += 1
                            continue
                count += 1
            continue
        await ctx.send(f"Sorry, I wasn't able to find anything that matches the given arguments.")


def flag_checks(message: discord.Message, flags):
    if flags.has_:
        if flags.has_ not in message.content:
            return False
    if flags.startswith_:
        if not message.content.startswith(flags.startswith_):
            return False
    if flags.endswith_:
        if not message.content.endswith(flags.endswith_):
            return False
    return True


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


async def re_iter(flags: ExecuteFlags, local_vars: dict, say_say, embeds_say, match=None, string=None, pattern=None):
    with contextlib.redirect_stdout(io.StringIO()):
        if string or pattern:
            matches = re.finditer(string=string, pattern=pattern)
            for match in matches:
                say_say = say_say.replace(flags.say_[match.start():match.end()], "")
                exec(
                    f"async def func():\n{textwrap.indent(f'return {flags.say_[match.start():match.end()]}', '    ')}", local_vars)
                obj: object = await local_vars["func"]()
                embeds_say.append(obj)
                return say_say, embeds_say

        if match:
            say_say = say_say.replace(flags.say_[match.start():match.end()], "")
            exec(f"async def func():\n{textwrap.indent(f'return {flags.say_[match.start():match.end()]}', '    ')}", local_vars)
            obj: object = await local_vars["func"]()
            embeds_say.append(obj)
            return say_say, embeds_say


def setup(bot):
    bot.add_cog(RootInvoke(bot))