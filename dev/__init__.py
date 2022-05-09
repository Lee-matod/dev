# -*- coding: utf-8 -*-

"""
dev
~~~

A simple debugging, editing and testing extension for discord.py.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from dev.__main__ import *
from dev.handlers import *
from dev.converters import *

from dev.config.bot import RootBot
from dev.config.over import RootOverride
from dev.config.variables import RootVariables
from dev.experimental.http import RootHTTP
from dev.experimental.invoke import RootInvoke
from dev.experimental.python import RootPython
from dev.flags.flags import RootFlags

from dev.utils.utils import *
from dev.utils.functs import *
from dev.utils.startup import *
from dev.utils.baseclass import *

__all__ = (
    "Command",
    "Dev",
    "Group",
    "VirtualVarReplacer",
    "codeblock_converter",
    "local_globals",
    "Root",
    "root",
    "send",
    "Settings"
)

cogs = [RootCommand, RootBot, RootOverride, RootVariables, RootHTTP, RootInvoke, RootPython, RootFlags]


class Dev(*cogs):
    """
    The frontend Root cog of the dev extension.
    """


async def setup(bot: commands.Bot):
    await set_settings(bot)
    await bot.add_cog(Dev(bot))
    await setup_(bot)
