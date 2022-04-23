# -*- coding: utf-8 -*-

"""
dev.experimental.python
~~~~~~~~~~~~~~~~~~~~~~~

Direct evaluation or execution of Python code.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""

import io
import discord
import textwrap
import contextlib

from discord.ext import commands

from dev.converters import __previous__
from dev.handlers import ExceptionHandler, VirtualVarReplacer

from dev.utils.startup import settings
from dev.utils.baseclass import root, Root
from dev.utils.functs import clean_code, send


try:
    import aioconsole
except ImportError:
    aexec = False
else:
    aexec = True


class RootPython(Root):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @root.command(name="python", parent="dev", version=1.1, supports_virtual_vars=True, aliases=["py"])
    async def root_python(self, ctx: commands.Context, *, code: str):
        """Evaluate or execute Python code.
        When specifying a script, some placeholder texts can be set.
        `__previous__` = This is replaced with the previous script that was executed. The bot will search through the history of the channel with a limit of 200 messages.
        `|root|` = Replaced with the root folder specified in `settings["folder"]["root_folder"]`.
        """
        local = {"discord": discord, "commands": commands, "bot": self.bot, "ctx": ctx}
        stdout = io.StringIO()

        with VirtualVarReplacer(settings, code) as decoded_code:
            code = decoded_code.replace("|root|", settings["root_folder"])
            code = await __previous__(ctx, code)
            # Since eval can't be async, and doing 'asyncio.run(compile(code, filename, "eval"))' isn't really neat,
            # we automatically add a return statement so code such as 'dev python "abc foo"' would return the string
            #   instead of just executing it
            code = clean_code(code if '\n' in code else f"return {code}" if not code.strip().startswith("return") or not code.strip().startswith("yield") else code)

        with contextlib.redirect_stdout(stdout):
            async with ExceptionHandler(ctx.message):
                if aexec:
                    await aioconsole.aexec(f"async def func():\n{textwrap.indent(code, '    ')}", local)
                else:
                    exec(f"async def func():\n{textwrap.indent(code, '    ')}", local)
                return_ = await local["func"]()
                value = stdout.getvalue()
                res_ret = (f"```py\n{value}\n```" if value else '') + (f"```py\n{return_}\n```" if return_ else '')
                if res_ret:
                    return await send(ctx, embed=discord.Embed(title="Output", description=f"{res_ret}", color=discord.Color.green()))