# -*- coding: utf-8 -*-

"""
dev.utils.startup
~~~~~~~~~~~~~~~~~

Functions and variables that will get executed once the dev extension is loaded.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""

import os

from discord.ext import commands
from typing import Optional, Dict, List

from dev.utils.baseclass import root

__all__ = (
    "cogs",
    "get_owner",
    "set_cogs",
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

owner: List[int]
cogs: Dict[str, commands.Cog] = {}


def set_settings(bot: commands.Bot) -> None:
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

    global owner
    if not [bot.owner_ids, bot.owner_id, settings["owners"]]:
        raise TypeError("For security reasons, please set owner id(s) when using the dev module.")
    owner = bot.owner_ids or [bot.owner_id]
    check_types()


def check_types() -> None:
    """Check if the values specified in :var:`settings` are valid types.

    Raises
    ------
    ValueError
        Invalid type found for a value.
    """
    setting_types = {"path_to_file": str, "root_folder": str, "virtual_vars_format": str, "owners": (list, tuple, set)}
    for module, _type in setting_types.items():
        if not isinstance(settings[module], _type):
            raise ValueError(f"invalid type for 'settings[{module}]'. Expected {', '.join(sett.__name__ for sett in setting_types[module])} but received {settings[module].__class__.__name__}")

    if not settings["virtual_vars_format"]:
        raise ValueError(f"settings[\"virtual_vars_format\"] cannot be None")


def get_owner() -> List[int]:
    """Returns the list of user IDs that can use dev commands

    Returns
    -------
    List[int]
        A list of user IDs that are allowed to use the dev extension.
    """
    return owner


def set_cogs(**kwargs) -> None:
    global cogs
    for name, inst in kwargs.items():
        cogs[name] = inst


async def setup_(bot: commands.Bot, *args) -> None:
    """Makes sure commands are loaded properly and added with their respective parents.

    Parameters
    ----------
    bot: :class:`commands.Bot`
        Used to load the appropriate cogs and
        delete any standalone dev commands that have already been assigned to a parent.

    args: :class:`str`
        Extension names
    """
    for ext in args:
        try:
            await bot.load_extension(ext)
        except commands.ExtensionAlreadyLoaded:
            await bot.unload_extension(ext)
            await bot.load_extension(ext)

    for cmd, parent_name in root._add_parent.items():
        parent: Optional[commands.Group] = bot.get_command(parent_name)
        parent.add_command(cmd)
        bot.remove_command(cmd.name)
