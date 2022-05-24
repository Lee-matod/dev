# -*- coding: utf-8 -*-

"""
dev
~~~

A simple debugging, editing and testing extension for discord.py version 2.0 (master).

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""

__version__ = "1.0.0a"


from dev.__main__ import *
from dev.converters import *
from dev.handlers import *

from dev.config import RootBot, RootManagement, RootOver, RootVariables
from dev.experimental import RootHTTP, RootInvoke, RootPython
from dev.flags import RootFlags

from dev.utils.baseclass import *
from dev.utils.functs import *
from dev.utils.startup import *
from dev.utils.utils import *


__all__ = (
    "CodeblockConverter",
    "Command",
    "Dev",
    "GlobalLocals",
    "Group",
    "Root",
    "Settings",
    "replace_vars",
    "root",
    "send"
)

cogs = [RootBot, RootCommand, RootFlags, RootHTTP, RootInvoke, RootManagement, RootOver, RootPython, RootVariables]


class Dev(*cogs):
    """
    The frontend root cog of the dev extension.
    """


async def setup(bot: commands.Bot):
    await set_settings(bot)
    await bot.add_cog(Dev(bot))
    await setup_(bot)
