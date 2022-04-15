from typing import *

import io
import discord
import asyncio
import textwrap
import contextlib
import aioconsole

from traceback import format_exception
from discord.ext import commands

from dev.utils.baseclass import root
from dev.utils.startup import set_cogs
from dev.utils.functs import clean_code, is_owner, send


class RootPython(commands.Cog):
    error: Optional[List[Exception]] = [None]

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @root.command(name="python", parent="dev", version=1.1, aliases=["py"])
    @is_owner()
    async def root_python(self, ctx: commands.Context, *, code: str):
        """
        Evaluate or execute Python code.
        An arguments can be given before specifying the script to change its behaviour.
        `lines`|`func` = Shows the whole code without executing it and adds line numbers.
        `debug`|`dbg` = If an error occurs, the bot will send the traceback instead of reacting with a ❗. The time that the script took to run will also be recorded.
        When specifying a script, some placeholder texts can be set.
        `__previous__` = This is replaced with the previous script that was executed. The bot will search with a history length of 100. You may also set line limiters: `__previous__[start:end]`.
        `/root/` = Replaced with the root folder specified in `settings["folder"]["root_folder"]`.
        When setting `settings["folder"]["path_to_file"]`, this _str_ will be the replacement for a tracebacks' file path.
        """
        # TODO: - rewrite this command
        error: Optional[List[Exception]] = getattr(RootPython, "error")  # `self` is passed as :type commands.Context: hence why we use `getattr` to get our class attributes.
        error.clear()
        local = {"discord": discord, "commands": commands, "bot": self.bot, "ctx": ctx}
        code = clean_code(code)
        code = code if '\n' in code else f"return {code}" if not code.strip().startswith("return") or not code.strip().startswith("yield") else code
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            try:
                await aioconsole.aexec(f"async def func():\n{textwrap.indent(code, '    ')}", local)
                return_ = await local["func"]()
                value = stdout.getvalue()
                res_ret = (f"```py\n{value}\n```" if value else '') + (f"```py\n{return_}\n```" if return_ else '')
                await ctx.message.add_reaction("☑")
                if res_ret:
                    return await send(ctx, embed=discord.Embed(title="Output", description=f"{res_ret}", color=discord.Color.green()))

            except (EOFError, IndentationError, RuntimeError, SyntaxError, TimeoutError, asyncio.TimeoutError) as e:
                await ctx.message.add_reaction("💢")
                error.append(e)
            except (AssertionError, ImportError, ModuleNotFoundError, UnboundLocalError) as e:
                await ctx.message.add_reaction("❓")
                error.append(e)
            except (AttributeError, IndentationError, KeyError, NameError, TypeError, UnicodeError, ValueError, commands.CommandInvokeError) as e:
                await ctx.message.add_reaction("❗")
                error.append(e)
            except ArithmeticError as e:
                await ctx.message.add_reaction("⁉")
                error.append(e)
            except (EnvironmentError, IOError, OSError, SystemError, SystemExit, WindowsError) as e:
                await ctx.message.add_reaction("‼")
                error.append(e)


async def setup(bot):
    ext = RootPython(bot)
    set_cogs(RootPython=ext)
    await bot.add_cog(RootPython(bot))