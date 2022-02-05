import discord
import re
import contextlib
import textwrap
import io
import shlex

from discord.ext import commands
from typing import Optional

from dev.utils.functs import is_owner
from dev.utils.settings import settings


class ExecuteFlags(commands.FlagConverter):
    command_: Optional[str] = commands.flag(name="command", default=None)
    kwargs_: Optional[str] = commands.flag(name="kwargs", default={})
    args_: Optional[str] = commands.flag(name="args", default=())
    as_: Optional[discord.Member] = commands.flag(name="as", default=None)
    at_: Optional[discord.TextChannel] = commands.flag(name="at", default=None)
    say_: Optional[str] = commands.flag(name="say", default=None)
    dm_: Optional[discord.Member] = commands.flag(name="dm", default=None)


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

    @commands.group(name="execute", invoke_without_command=True, aliases=["exec"])
    @is_owner()
    async def root_execute(self, ctx: commands.Context, *, flags: ExecuteFlags):
        flags.args_ = shlex.split(flags.args_)
        new_ctx = await self.bot.get_context(ctx.message, cls=CContext)
        new_ctx.set_properties(flags.as_ or ctx.author, flags.at_ or ctx.channel)
        kwargs_dict = {}
        if flags.kwargs_:
            kwargs = shlex.split(flags.kwargs_)
            compiler = self.convert_kwargs_format(settings["kwargs"]["format"])
            kwargs_pattern = re.compile(rf"{compiler}")
            for kw in kwargs:
                match = re.finditer(string=kw, pattern=kwargs_pattern)
                if match:
                    for m in match:
                        key, word = m.group().split(settings['kwargs']['separator'], 1)
                        kwargs_dict[key] = word

        if flags.command_:
            try:
                command: commands.Command = self.bot.get_command(flags.command_)
                return await command.__call__(new_ctx, *flags.args_, **kwargs_dict)
            except Exception as e:
                return await ctx.send(embed=discord.Embed(title=e.__class__.__name__, description=f"```py\n{e}\n```", color=discord.Color.red()))

        if flags.say_:
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