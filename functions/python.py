import discord
import contextlib
import io
import textwrap
import time

from discord.ext import commands
from traceback import format_exception

from dev.utils.functs import clean_code, is_owner
from dev.utils.settings import settings


class RunEval(discord.ui.View):
    def __init__(self, ctx: commands.Context, code, eval_cmd):
        super().__init__()
        self.ctx = ctx
        self.code = code
        self.eval_cmd = eval_cmd

    @discord.ui.button(label="Run", style=discord.ButtonStyle.green, emoji="▶")
    async def eval_run(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            return
        embed = await self.eval_cmd(self.code, self.ctx, lines=True)
        if embed:
            return await interaction.message.edit(embed=embed, view=None)
        return await interaction.message.add_reaction("❗")


class RootPython(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(name="python", aliases=["py"])
    @is_owner()
    async def root_eval(self, ctx: commands.Context, *, code: str):
        args = ""
        for arg in code.split():
            if "```" in arg:
                break
            elif arg not in ["lines", "def", "debug", "dbg"]:
                continue
            args += f"{arg} "
        code = clean_code(code[len(args):].strip())
        kwargs = {}
        if args:
            for arg in args.split():
                kwargs[arg] = True
        if "lines" in args or "def" in args:
            if len(args.split()) > 1:
                return await ctx.reply(f"`{self.bot.command_prefix}dev py` cannot take other arguments when using `lines`|`def`.")
        if "/root/" in code:
            code = code.replace("/root/", settings["folder"]["root_folder"])
        embed = await self.eval(code, ctx, kwargs)
        if embed:
            return await ctx.send(embed=embed)

    async def eval(self, code, ctx: commands.Context, kwargs: dict):
        messages = await ctx.channel.history(limit=100).flatten()
        for message in messages:
            if message.author.id == ctx.author.id:
                if message.content.startswith("?dev py"):
                    if "__previous__" in message.content:
                        continue
                    else:
                        previous_code = message.content.removeprefix("?dev py ")
                        previous_code = clean_code(previous_code[previous_code.find("`"):])
                        if "__previous__" in code:
                            code = code.replace("__previous__", previous_code)
                        break
                else:
                    continue
            else:
                continue
        debug = kwargs.pop("debug", False) or kwargs.pop("dbg", False)
        lines = kwargs.pop("lines", False) or kwargs.pop("def", False)
        if lines:
            return await self.eval_def(code)
        local_vars = {
            "discord": discord,
            "commands": commands,
            "bot": self.bot,
            "ctx": ctx,
        }

        stdout = io.StringIO()
        embed = discord.Embed(title="Console" if not debug else "Debug Console")
        try:
            with contextlib.redirect_stdout(stdout):
                start = time.perf_counter()
                exec(f"async def func():\n{textwrap.indent(code, '    ')}", local_vars)
                obj = await local_vars["func"]()
                res = f"{stdout.getvalue()}\n-- {obj}"
                embed.description = f"```py\n{res}\n```"
                embed.colour = discord.Color.green()
                end = time.perf_counter()
                if debug:
                    embed.set_footer(text=f"Script took {end - start:.3f} seconds.")
                await ctx.message.add_reaction("☑")
                return embed
        except Exception as e:
            if debug:
                res = "".join(format_exception(e, e, e.__traceback__))
                if settings["folder"]["path_to_file"]:
                    res.replace(settings["folder"]["path_to_file"], "/path/to/file/")
                embed.description = f"```py\n{res}\n```"
                embed.colour = discord.Color.red()
                end = time.perf_counter()
                embed.set_footer(text=f"Script took {end - start:.3f} seconds.")
                return embed
            await ctx.message.add_reaction("❗")
            return False

    async def eval_def(self, code) -> discord.Embed:
        indented_code = textwrap.indent(code, '    ')
        indented_code_split = indented_code.split("\n") if indented_code.split("\n")[-1] != '' else indented_code.split("\n")[:-len([a for a in indented_code.split("\n") if a == ''])]
        obj = ""
        for c in range(len(indented_code_split)):
            obj += f"{c + 2}. | {indented_code_split[c]}\n"
        res = f"```py\n" \
              f"1. | async def func():\n" \
              f"{obj}" \
              f"```"
        embed = discord.Embed(title="File", description=res, color=discord.Color.gold())
        return embed


def setup(bot: commands.Bot):
    bot.add_cog(RootPython(bot))