# -*- coding: utf-8 -*-

"""
dev.experimental.python
~~~~~~~~~~~~~~~~~~~~~~~

Direct evaluation or execution of Python code.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""

from typing import *

import io
import discord
import asyncio
import textwrap
import contextlib

from discord.ext import commands

from dev.utils.startup import set_cogs, settings
from dev.utils.functs import clean_code, is_owner, send
from dev.utils.baseclass import root, VirtualVarReplacer

try:
    import aioconsole
    aexec = True
except ImportError:
    aexec = False


class RootPython(commands.Cog):
    error: Optional[List[Exception]] = [None]

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @root.command(name="python", parent="dev", version=1.1, supports_virtual_vars=True, aliases=["py"])
    @is_owner()
    async def root_python(self, ctx: commands.Context, *, code: str):
        """Evaluate or execute Python code.
        When specifying a script, some placeholder texts can be set.
        `__previous__` = This is replaced with the previous script that was executed. The bot will search through the history of the channel with a limit of 200 messages.
        `|root|` = Replaced with the root folder specified in `settings["folder"]["root_folder"]`.
        """
        error: Optional[List[Exception]] = getattr(RootPython, "error")  # `self` is passed as commands.Context hence why we use `getattr` to get our class attributes.
        error.clear()
        local = {"discord": discord, "commands": commands, "bot": self.bot, "ctx": ctx}
        # Since eval can't be async, and doing 'asyncio.run(compile(code, filename, "eval"))' isn't really neat,
        # we automatically add a return statement so code such as 'dev python "abc foo"' would return the string instead of just executing it
        with VirtualVarReplacer(settings, code) as decoded_code:
            code = decoded_code.replace("|root|", settings["root_folder"])
            code = await __previous__(ctx, code)
            code = clean_code(code if '\n' in code else f"return {code}" if not code.strip().startswith("return") or not code.strip().startswith("yield") else code)
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            try:
                if aexec:
                    await aioconsole.aexec(f"async def func():\n{textwrap.indent(code, '    ')}", local)
                else:
                    exec(f"async def func():\n{textwrap.indent(code, '    ')}", local)
                return_ = await local["func"]()
                value = stdout.getvalue()
                res_ret = (f"```py\n{value}\n```" if value else '') + (f"```py\n{return_}\n```" if return_ else '')
                await ctx.message.add_reaction("☑")
                if res_ret:
                    return await send(ctx, embed=discord.Embed(title="Output", description=f"{res_ret}", color=discord.Color.green()))

            # Now time to have fun with errors.
            # This is completely unnecessary, but it's fun and makes it more interactive
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


async def __previous__(ctx: commands.Context, code: str, /):
    previous = code
    if "__previous__" in code:
        skip = 0  # if we don't do this, then ctx.message would be the first message and would probably break everything
        async for message in ctx.message.channel.history(limit=200):
            if skip:
                if message.author == ctx.author:
                    if message.content.startswith(f"{ctx.prefix}dev py"):
                        previous = previous.replace("__previous__", clean_code(message.content.lstrip(f"{ctx.prefix}dev py").strip()))
                    if message.content.startswith(f"{ctx.prefix}dev python"):
                        previous = previous.replace("__previous__", clean_code(message.content.lstrip(f"{ctx.prefix}dev python").strip()))
                    if "__previous__" not in previous:
                        # No need to continue iterating through messages
                        # if '__previous__' isn't requested anymore
                        break
            else:
                skip += 1
    return previous


async def setup(bot):
    ext = RootPython(bot)
    set_cogs(RootPython=ext)
    await bot.add_cog(RootPython(bot))