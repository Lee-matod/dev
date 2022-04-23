# -*- coding: utf-8 -*-

"""
dev.utils.startup
~~~~~~~~~~~~~~~~~

Functions and variables that will get executed once the dev extension is loaded.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""

import os

from typing import Optional
from discord.ext import commands

from dev.utils.baseclass import root

__all__ = (
    "set_settings",
    "settings",
    "setup_"
)

settings = {
    "path_to_file": f"{os.getcwd()}",   # type: str
    "root_folder": "",  # type: str
    "virtual_vars_format": "|%(name)s|",  # type: str
    "owners": []  # type: list, tuple, set
}


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
    global settings
    if not (bot.owner_ids, bot.owner_id, settings["owners"]):
        raise TypeError("For security reasons, please set owner id(s) when using the dev module.")
    if not settings["owners"]:
        data = await bot.application_info()
        settings["owners"] = [data.owner.id]
    check_types()


def check_types() -> None:
    setting_types = {"path_to_file": str, "root_folder": str, "virtual_vars_format": str, "owners": (list, tuple, set)}
    for module, _type in setting_types.items():
        if not isinstance(settings[module], _type):
            raise ValueError(f"invalid type for 'settings[{module}]'. Expected {', '.join(sett.__name__ for sett in setting_types[module])} but received {settings[module].__class__.__name__}")

    if not settings["virtual_vars_format"]:
        raise ValueError(f"settings[\"virtual_vars_format\"] cannot be None")


async def setup_(bot: commands.Bot) -> None:
    """Makes sure commands are loaded properly and added with their respective parents.

    Parameters
    ----------
    bot: :class:`commands.Bot`
        Used to load the appropriate cogs and
        delete any standalone dev commands that have already been assigned to a parent.
    """
    for cmd, parent_name in root._add_parent.items():
        parent: Optional[commands.Group] = bot.get_command(parent_name)
        parent.add_command(cmd)
        bot.remove_command(cmd.name)
