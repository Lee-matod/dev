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
    repeat_: Optional[int] = commands.flag(name="repeat", default=1)


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


class RootExecute(commands.Cog):
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

        for _ in range(flags.repeat_):
            if flags.repeat_ > 20:
                return await ctx.send("I'm sorry, but I cannot repeat these arguments more than 20 times.")

            elif flags.command_:
                if flags.repeat_ == 1:
                    try:
                        command: commands.Command = self.bot.get_command(flags.command_)
                        if command is None:
                            return await ctx.send(f"Command `{flags.command_}` is not found.")
                        return await command.__call__(new_ctx, *flags.args_, **kwargs_dict)

                    except Exception as e:
                        return await ctx.send(embed=discord.Embed(title=e.__class__.__name__, description=f"```py\n{e}\n```", color=discord.Color.red()))
                alt_ctx: commands.Context = await self.generate_ctx(ctx, flags.as_ or ctx.author, flags.at_ or ctx.channel, content=f"{ctx.prefix}{flags.command_}")
                if alt_ctx.command is None:
                    return await ctx.send(f"Command `{flags.command_}` is not found.")
                await alt_ctx.command.reinvoke(alt_ctx)

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
    async def root_reinvoke(self, ctx: commands.Context, history_length: int = 1, command: bool = True):
        messages = await ctx.channel.history(limit=100).flatten()
        count = 1
        for message in messages:
            if message.author.id == ctx.author.id:
                if count == history_length:
                    if command and message.content.startswith(ctx.prefix):
                        if message.content.lstrip(ctx.prefix).split(" ", 2)[:2] == ["dev", "reinvoke"]:
                            history_length += 1
                            continue
                        alt_ctx: commands.Context = await self.generate_ctx(ctx, ctx.author, ctx.channel, content=message.content)
                        return await alt_ctx.command.reinvoke(alt_ctx)
                    elif not command:
                        return await ctx.send(embed=discord.Embed(title="Last Message", description=f"{message.author.mention} said:\n{message.content}", url=message.jump_url))
                count += 1
            continue
        await ctx.send("Couldn't find anything.")

    async def generate_ctx(self, ctx: commands.Context, author: discord.Member, channel: discord.TextChannel, **kwargs) -> commands.Context:
        msg: discord.Message = copy(ctx.message)
        msg._update(kwargs)
        msg.author = author
        msg.channel = channel
        return await self.bot.get_context(msg, cls=type(ctx))

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
    bot.add_cog(RootExecute(bot))