# -*- coding: utf-8 -*-

"""
dev.utils.startup
~~~~~~~~~~~~~~~~~

Functions and variables that will get executed once the dev extension is loaded.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""

import re
import os
import collections.abc

from discord.ext import commands
from typing import Collection, Optional

from dev.utils.baseclass import root, Group

__all__ = (
    "set_settings",
    "virtual_vars_format",
    "Settings",
    "setup_"
)


class Settings:
    MENTION_AUTHOR: Optional[bool] = True
    INVOKE_ON_EDIT: Optional[bool] = True
    OWNERS: Optional[Collection[int]] = []
    PATH_TO_FILE: Optional[str] = f"{os.getcwd()}"
    ROOT_FOLDER: Optional[str] = ""
    VIRTUAL_VARS: str = "|%(name)s|"


async def set_settings(bot: commands.Bot) -> None:
    """Set owner IDs that will be able to use the extension upon loading.

    Calls :meth:`check_types` if no issues were found.

    Parameters
    ----------
    bot: :clss:`commands.Bot`
        Check if there are any already specified owner IDs within the bot build.

    Raises
    ------
    TypeError
        No user IDs were specified.
    """
    if not Settings.OWNERS:
        data = await bot.application_info()
        Settings.OWNERS = [data.owner.id]
    check_types()


def check_types() -> None:
    setting_types = (
        [Settings.MENTION_AUTHOR, bool, "MENTION_AUTHOR"],
        [Settings.INVOKE_ON_EDIT, bool, "INVOKE_ON_EDIT"],
        [Settings.OWNERS, collections.abc.Collection, "OWNERS"],
        [Settings.PATH_TO_FILE, str, "PATH_TO_FILE"],
        [Settings.ROOT_FOLDER, str, "ROOT_FOLDER"],
        [Settings.VIRTUAL_VARS, str, "VIRTUAL_VARS"]
    )
    for module in setting_types:
        received, expected, var = module
        if not isinstance(received, expected):
            raise ValueError(f"invalid type for Settings.{var}. Expected {expected.__class__!r} but received {type(received).__class__!r}")

    if not Settings.VIRTUAL_VARS:
        raise ValueError(f"Settings.VIRTUAL_VARS cannot be None")


def virtual_vars_format() -> str:
    format_style = re.compile(r"(%\(name\)s)")
    match = re.search(format_style, Settings.VIRTUAL_VARS)
    compiler = "("
    added = False
    for i in range(len(Settings.VIRTUAL_VARS)):
        if i in range(match.start(), match.end()):
            if match and not added:
                compiler += r"(.+?)"
                added = True
                continue
            continue
        elif Settings.VIRTUAL_VARS[i] in [".", "^", "$", "*", "+", "?", "{", "[", "(", ")", "|"]:
            compiler += f"\\{Settings.VIRTUAL_VARS[i]}"
            continue
        compiler += Settings.VIRTUAL_VARS[i]
    compiler += ")"
    return compiler


async def setup_(bot: commands.Bot) -> None:
    root_command: Optional[Group] = bot.get_command("dev")
    for cmd, parent in root._add_parent.items():
        root_command.add_command(cmd)
        bot.remove_command(cmd.name)