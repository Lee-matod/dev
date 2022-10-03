# -*- coding: utf-8 -*-

"""
dev.utils.startup
~~~~~~~~~~~~~~~~~

Extension loading function and settings checker.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import re
import os
import pathlib
from typing import Set

from dev import types


__all__ = (
    "Settings",
    "set_settings",
)


class Settings:
    """
    ALLOW_GLOBAL_USES: :class:`bool`
        Commands that have their `global_use` property set True are allowed to be invoked by any user.
        Defaults to `False`.
    FLAG_DELIMITER: :class:`str`
        The characters that determine when to separate a key from its valur when parsing strings to dictionaries.
        Defaults to `=``
    INVOKE_ON_EDIT: :class:`bool`
        If enabled, whenever a message with a command is edited to another command, the bot will try to invoke the new
        command.
        Defaults to `False`.
    OWNERS: Set[:class:`int`]
        A set of user IDs that override bot ownership IDs, thus allowing these users to use this extension.
    PATH_TO_FILE: :class:`str`
        A path directory that will be removed if found inside a message. This will typically be used in tracebacks.
        Defaults to your current working directory.
    ROOT_FOLDER: :class:`str`
        The path that will replace the `|root|` text placeholder.
    VIRTUAL_VARS: :class:`str`
        The format in which virtual variables should be specified. The actual place where the
        variable's name will be should be defined as `$var$`.
        Defaults to `|$var$|`.
    """

    ALLOW_GLOBAL_USES: bool = False
    FLAG_DELIMITER: str = "="
    INVOKE_ON_EDIT: bool = False
    OWNERS: Set[int] = {}
    PATH_TO_FILE: str = os.getcwd()
    ROOT_FOLDER: str = ""
    VIRTUAL_VARS: str = "|$var$|"


async def set_settings(bot: types.Bot) -> None:
    if not Settings.OWNERS:
        try:
            if bot.application.owner:
                Settings.OWNERS = {bot.application.owner.id}
            elif bot.application.team:
                Settings.OWNERS = {owner.id for owner in bot.application.team.members}
        except AttributeError:
            Settings.OWNERS = set()
    check_types(bot)


def check_types(bot: types.Bot) -> None:
    setting_types = (
        [Settings.FLAG_DELIMITER, str, "FLAG_DELIMITER"],
        [Settings.INVOKE_ON_EDIT, bool, "INVOKE_ON_EDIT"],
        [Settings.OWNERS, set, "OWNERS"],
        [Settings.PATH_TO_FILE, str, "PATH_TO_FILE"],
        [Settings.ROOT_FOLDER, str, "ROOT_FOLDER"],
        [Settings.ALLOW_GLOBAL_USES, bool, "ALLOW_GLOBAL_USES"],
        [Settings.VIRTUAL_VARS, str, "VIRTUAL_VARS"]
    )
    if not any((bot.owner_id, bot.owner_ids, Settings.OWNERS)):
        raise ValueError("For security reasons, an owner ID must be set")

    for module in setting_types:
        received, expected, var = module
        if not isinstance(received, expected):
            raise ValueError(
                f"invalid type for Settings.{var}. "
                f"Expected {expected.__name__} but received {type(received).__name__}"
            )

    if not Settings.VIRTUAL_VARS:
        raise ValueError("Settings.VIRTUAL_VARS cannot be None")

    elif len([_ for _ in re.finditer(r"\$var\$", Settings.VIRTUAL_VARS)]) != 1:
        raise ValueError(f"Settings.VIRTUAL_VARS got 0 or more than 1 instance of '$var$', exactly 1 expected")

    if not Settings.FLAG_DELIMITER:
        raise ValueError("Settings.FLAG_DELIMITER cannot be None")

    if Settings.FLAG_DELIMITER.strip() == ":":
        raise ValueError("Settings.FLAG_DELIMITER cannot be ':'")

    if Settings.ROOT_FOLDER:
        root_folder = pathlib.Path(Settings.ROOT_FOLDER)
        if not root_folder.exists():
            raise ValueError(f"Path {Settings.ROOT_FOLDER} does not exist")
        elif root_folder.is_file():
            raise ValueError(f"Path {Settings.ROOT_FOLDER} is a file, not a directory")

    if Settings.PATH_TO_FILE:
        path = pathlib.Path(Settings.PATH_TO_FILE)
        if not path.exists():
            raise ValueError(f"Path {Settings.PATH_TO_FILE!r} does not exist")
