# -*- coding: utf-8 -*-

"""
dev
~~~

A simple debugging, editing and testing extension for discord.py.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from typing import *

from dev.__main__ import *
from dev.handlers import *

from dev.config.bot import RootBot
from dev.config.over import RootOverride
from dev.config.variables import RootVariables
from dev.experimental.http import RootHTTP
from dev.experimental.invoke import RootInvoke
from dev.experimental.python import RootPython
from dev.flags.flags import RootFlags
from dev.flags.help_command import RootHelp

from dev.utils.utils import *
from dev.utils.functs import *
from dev.utils.startup import *
from dev.utils.baseclass import *

__all__ = (
    "Command",
    "Dev",
    "Group",
    "StringCodeblockConverter",
    "VirtualVarReplacer",
    "is_owner",
    "local_globals",
    "Root",
    "root",
    "send",
    "settings"
)

cogs: List[commands.Cog] = [getattr(module, name) for module, name in root._cogs.items()]


class Dev(*cogs):
    """
    The frontend subclassed Root cog of the dev extension.
    """


async def setup(bot: commands.Bot):
    await set_settings(bot)
    await bot.add_cog(Dev(bot))
    await setup_(bot)