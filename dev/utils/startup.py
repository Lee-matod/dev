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

from discord.ext import commands
from typing import Optional, Set

from dev.utils.baseclass import Group, root


__all__ = (
    "Settings",
    "set_settings",
    "setup_"
)


class Settings:
    FLAG_DELIMITER: str = "="
    INVOKE_ON_EDIT: bool = True
    OWNERS: Optional[Set[int]] = {}
    PATH_TO_FILE: Optional[str] = f"{os.getcwd()}"
    ROOT_FOLDER: Optional[str] = ""
    VIRTUAL_VARS: str = "|$var$|"


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
        try:
            data = await bot.application_info()
            Settings.OWNERS = {data.owner.id}
        except AttributeError:
            pass
    check_types()


def check_types() -> None:
    setting_types = (
        [Settings.FLAG_DELIMITER, str, "FLAG_DELIMITER"],
        [Settings.INVOKE_ON_EDIT, bool, "INVOKE_ON_EDIT"],
        [Settings.OWNERS, set, "OWNERS"],
        [Settings.PATH_TO_FILE, str, "PATH_TO_FILE"],
        [Settings.ROOT_FOLDER, str, "ROOT_FOLDER"],
        [Settings.VIRTUAL_VARS, str, "VIRTUAL_VARS"]
    )
    for module in setting_types:
        received, expected, var = module
        if not isinstance(received, expected):
            raise ValueError(f"invalid type for Settings.{var}. Expected {expected.__name__!r} but received {type(received).__name__!r}")

    if not Settings.VIRTUAL_VARS:
        raise ValueError("Settings.VIRTUAL_VARS cannot be None")

    elif len([_ for _ in re.finditer(r"\$var\$", Settings.VIRTUAL_VARS)]) != 1:
        raise ValueError(f"Settings.VIRTUAL_VARS got 0 or more than 1 instance of '$var$', exactly 1 expected")

    if not Settings.FLAG_DELIMITER:
        raise ValueError("Settings.FLAG_DELIMITER cannot be None")

    if Settings.FLAG_DELIMITER.strip() == ":":
        raise ValueError("Settings.FLAG_DELIMITER cannot be ':' as it may interfere with dictionary parsing")


async def setup_(bot: commands.Bot) -> None:
    root_command: Optional[Group] = bot.get_command("dev")
    for cmd, parent in root._add_parent.items():
        root_command.add_command(cmd)
        bot.remove_command(cmd.name)
        
