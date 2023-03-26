# -*- coding: utf-8 -*-

"""
dev
~~~

A simple debugging, editing and testing extension for discord.py version 2.0.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""

__title__ = "dev"
__author__ = "Lee"
__license__ = "MIT"
__copyright__ = "Copyright 2022-present Lee (Lee-matod)"
__version__ = "2.0.0a"

from typing import Literal, NamedTuple

from discord.ext import commands

from dev.components import *
from dev.converters import *
from dev.handlers import *
from dev.interpreters import *
from dev.pagination import *
from dev.plugins import *
from dev.registrations import *
from dev.types import *
from dev.utils.baseclass import *
from dev.utils.functs import *
from dev.utils.startup import *
from dev.utils.utils import *

__all__ = (
    "AuthoredView",
    "BaseCommandRegistration",
    "BoolInput",
    "CommandRegistration",
    "Dev",
    "ExceptionHandler",
    "Execute",
    "GlobalLocals",
    "GlobalTextChannelConverter",
    "LiteralModes",
    "ManagementOperation",
    "ManagementRegistration",
    "MessageCodeblock",
    "ModalSender",
    "Over",
    "OverType",
    "Process",
    "SettingRegistration",
    "Settings",
    "ShellSession",
    "TimedInfo",
    "clean_code",
    "codeblock_converter",
    "codeblock_wrapper",
    "escape",
    "format_exception",
    "interaction_response",
    "plural",
    "replace_vars",
    "send",
    "setup_logging",
    "str_bool",
    "str_ints",
)


class VersionInfo(NamedTuple):
    major: int
    minor: int
    micro: int
    releaselevel: Literal["alpha", "beta", "candidate", "final"]
    serial: int


version_info = VersionInfo(major=2, minor=0, micro=0, releaselevel="alpha", serial=0)


async def setup(bot: commands.Bot) -> None:
    _log = await enforce_owner(bot)
    await bot.add_cog(Dev(bot))
    _log.info("Dev cog has been successfully loaded")


del Literal, NamedTuple, commands
