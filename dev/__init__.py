# -*- coding: utf-8 -*-

"""
dev
~~~

A simple debugging, editing and testing extension for discord.py version 2.0.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from dev.__main__ import *
from dev.components import *
from dev.converters import *
from dev.handlers import *
from dev.interpreters import *
from dev.pagination import *
from dev.registrations import *
from dev.types import *

from dev.config import RootBot, RootManagement, RootOver, RootVariables
from dev.experimental import RootHTTP, RootInvoke, RootPython, RootShell
from dev.misc import RootFlags, RootSearch

from dev.utils.baseclass import *
from dev.utils.functs import *
from dev.utils.startup import *
from dev.utils.utils import *

__all__ = (
    "AuthoredView",
    "BaseCommandRegistration",
    "BoolInput",
    "CodeblockConverter",
    "CommandRegistration",
    "ExceptionHandler",
    "Execute",
    "GlobalLocals",
    "GlobalTextChannelConverter",
    "InteractionResponseType",
    "LiteralModes",
    "ManagementOperation",
    "ManagementRegistration",
    "ModalSender",
    "Over",
    "OverrideSettings",
    "OverType",
    "Process",
    "Root",
    "SettingRegistration",
    "Settings",
    "ShellSession",
    "SigKill",
    "TimedInfo",
    "clean_code",
    "codeblock_wrapper",
    "escape",
    "interaction_response",
    "optional_raise",
    "plural",
    "replace_vars",
    "root",
    "send",
    "setup_logging",
    "str_bool",
    "str_ints"
)

__title__ = "dev"
__author__ = "Lee"
__license__ = "Apache 2.0"
__version__ = "1.0.1a"


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
    RootShell,
    RootVariables
):
    """The frontend root cog of the dev extension that implements all features."""


async def setup(bot: commands.Bot) -> None:
    _log = await enforce_owner(bot)
    await bot.add_cog(Dev(bot))
    _log.info("Dev cog has been successfully loaded")
