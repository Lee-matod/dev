# -*- coding: utf-8 -*-

"""
dev
~~~

A simple debugging, editing and testing extension for discord.py version 2.0.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""

__title__ = "dev"
__author__ = "Lee"
__license__ = "Apache 2.0"
__version__ = "1.0.0a"


from dev.__main__ import *
from dev.converters import *
from dev.handlers import *

from dev.config import RootConfig
from dev.experimental import RootExperimental
from dev.flags import RootFlags

from dev.utils.baseclass import *
from dev.utils.functs import *
from dev.utils.startup import *
from dev.utils.utils import *


__all__ = (
    "BoolInput",
    "CodeblockConverter",
    "Command",
    "Dev",
    "ExceptionHandler",
    "GlobalLocals",
    "Group",
    "LiteralModes",
    "Paginator",
    "Root",
    "Settings",
    "convert_str_to_bool",
    "convert_str_to_ints",
    "flag_parser",
    "replace_vars",
    "root",
    "send"
)


class Dev(RootCommand, RootConfig, RootExperimental, RootFlags):
    """The frontend root cog of the dev extension."""


async def setup(bot: commands.Bot):
    await set_settings(bot)
    await bot.add_cog(Dev(bot))
    await setup_(bot)
