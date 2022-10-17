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
__version__ = "1.0.0rc"


from dev.__main__ import *
from dev.converters import *
from dev.handlers import *
from dev.pagination import *

from dev.config import RootBot, RootManagement, RootOver, RootVariables
from dev.experimental import RootHTTP, RootInvoke, RootPython
from dev.misc import RootFlags, RootSearch

from dev.utils.baseclass import *
from dev.utils.functs import *
from dev.utils.startup import *
from dev.utils.utils import *


__all__ = (
    "BoolInput",
    "CodeblockConverter",
    "Dev",
    "ExceptionHandler",
    "GlobalLocals",
    "Interface",
    "LiteralModes",
    "Paginator",
    "Root",
    "Settings",
    "all_commands",
    "clean_code",
    "str_bool",
    "str_ints",
    "escape",
    "flag_parser",
    "generate_ctx",
    "interaction_response",
    "plural",
    "replace_vars",
    "root",
    "send"
)


class Dev(
    RootBot,
    RootCommand,
    RootFlags,
    RootHTTP,
    RootInvoke,
    RootManagement,
    RootOver,
    RootPython,
    RootSearch,
    RootVariables
):
    """The frontend root cog of the dev extension that implements all features."""


async def setup(bot: commands.Bot) -> None:
    await set_settings(bot)
    await bot.add_cog(Dev(bot))
