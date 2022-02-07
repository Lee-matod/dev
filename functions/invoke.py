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


class CContext(commands.Context):
    def set_properties(self, a: discord.Member, c: discord.TextChannel):
        self.a = a
        self.c = c

    @property
    def author(self):
        return self.a

    @property
    def channel(self):
        return self.c


class RootInvoke(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_pattern = re.compile(r"discord\.Embed\(title=.*?\)((\.)?(add_field|set_footer|set_author)?\(?.*\)?)*")
        self.format_style = re.compile(r"%\((\w+)\)s")
        self.embeds_say = []
        self.say_say = ""

    @commands.command(name="execute", aliases=["exec"])
    @is_owner()
    async def root_execute(self, ctx: commands.Context, *, flags: ExecuteFlags):
        flags.args_ = shlex.split(flags.args_)
        new_ctx = await self.bot.get_context(ctx.message, cls=CContext)
        new_ctx.set_properties(flags.as_ or ctx.author, flags.at_ or ctx.channel)
        kwargs_dict = {}

        if flags.kwargs_:
            kwargs = shlex.split(flags.kwargs_)
            compiler = self.convert_kwargs_format(settings["kwargs"]["format"].strip())
            kwargs_pattern = re.compile(rf"{compiler}")
            for kw in kwargs:
                match = re.finditer(string=kw, pattern=kwargs_pattern)
                if match:
                    for m in match:
                        key, word = m.group().split(settings['kwargs']['separator'], 1)
                        kwargs_dict[key] = word

        elif flags.command_:
            try:
                command: commands.Command = self.bot.get_command(flags.command_)
                if command is None:
                    return await ctx.send(f"Command `{flags.command_}` is not found.")
                return await command.__call__(new_ctx, *flags.args_, **kwargs_dict)

            except Exception as e:
                return await ctx.send(embed=discord.Embed(title=e.__class__.__name__, description=f"```py\n{e}\n```", color=discord.Color.red()))

        elif flags.say_:
            matches = re.finditer(string=flags.say_, pattern=self.embed_pattern)
            self.say_say = flags.say_
            self.embeds_say = []
            kwargs = {}
            local_vars = {"ctx": new_ctx, "discord": discord}
            if matches:
                for match in matches:
                    if match.group().count("(") != match.group().count(")"):
                        amount = r".*?\)" * abs(match.group().count("(") - match.group().count(")"))
                        await self.re_iter(flags, local_vars, string=flags.say_, pattern=re.compile(r"discord\.Embed\(title=.*?\)" + amount + r"((\.)?(add_field|set_footer|set_author)?\(?.*\)?)*"))
                        continue
                    await self.re_iter(flags, local_vars, match=match)
            kwargs["content"] = self.say_say
            kwargs["embeds"] = self.embeds_say
            if flags.dm_:
                await flags.dm_.send(**kwargs)
                return await ctx.message.add_reaction("☑")
            return await new_ctx.send(**kwargs)

    @commands.command(name="reinvoke")
    @is_owner()
    async def root_reinvoke(self, ctx: commands.Context, *, flags: ReinvokeFlags):
        self.flags = flags

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
                    check = self.flag_checks(message)
                    if check:
                        if flags.jump_url_:
                            await ctx.send(embed=discord.Embed(title="Message URL", url=message.jump_url))

                        if flags.is_command_ and message.content.startswith(ctx.prefix):
                            alt_ctx: commands.Context = await self.generate_ctx(ctx, ctx.author, ctx.channel, content=message.content)
                            return await alt_ctx.command.reinvoke(alt_ctx)

                        if not flags.is_command_ and not message.content.startswith(ctx.prefix):
                            return await ctx.send(embed=discord.Embed(title=f"{flags.author_} said:", description=message.content, color=discord.Color.blurple()))

                        if not flags.is_command_ and message.content.startswith(ctx.prefix):
                            flags.skip_messages_ += 1
                            count += 1
                            continue
                count += 1
            continue
        await ctx.send(f"Sorry, I wasn't able to find anything that matches the given arguments.")

    def flag_checks(self, message: discord.Message):
        if self.flags.has_:
            if self.flags.has_ not in message.content:
                return False
        if self.flags.startswith_:
            if not message.content.startswith(self.flags.startswith_):
                return False
        if self.flags.endswith_:
            if not message.content.endswith(self.flags.endswith_):
                return False
        return True

    async def generate_ctx(self, ctx: commands.Context, author: discord.Member, channel: discord.TextChannel, **kwargs) -> commands.Context:
        alt_msg: discord.Message = copy(ctx.message)
        alt_msg._update(kwargs)
        alt_msg.author = author
        alt_msg.channel = channel
        return await self.bot.get_context(alt_msg, cls=type(ctx))

    def convert_kwargs_format(self, formatter: str):
        f = re.finditer(self.format_style, formatter)
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

    async def re_iter(self, flags: ExecuteFlags, local_vars: dict, match=None, string=None, pattern=None):
        with contextlib.redirect_stdout(io.StringIO()):
            if string or pattern:
                matches = re.finditer(string=string, pattern=pattern)
                for match in matches:
                    self.say_say = self.say_say.replace(flags.say_[match.start():match.end()], "")
                    exec(f"async def func():\n{textwrap.indent(f'return {flags.say_[match.start():match.end()]}', '    ')}", local_vars)
                    obj: object = await local_vars["func"]()
                    self.embeds_say.append(obj)
                    return
            if match:
                self.say_say = self.say_say.replace(flags.say_[match.start():match.end()], "")
                exec(f"async def func():\n{textwrap.indent(f'return {flags.say_[match.start():match.end()]}', '    ')}", local_vars)
                obj: object = await local_vars["func"]()
                self.embeds_say.append(obj)
                return


def setup(bot):
    bot.add_cog(RootInvoke(bot))