# -*- coding: utf-8 -*-

"""
dev.utils.startup
~~~~~~~~~~~~~~~~~

Extension loading function and settings checker.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import logging
import os
import pathlib
from typing import TYPE_CHECKING, Any, ClassVar

import discord
from discord.utils import MISSING, stream_supports_colour

if TYPE_CHECKING:
    from dev import types

__all__ = (
    "Settings",
    "enforce_owner",
    "setup_logging"
)


class _DefaultFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] BLANK%(name)s: %(message)s", "%Y/%m/%d %H:%M:%S")
        output = fmt.format(record)
        return output.replace("BLANK", " " * (8 - len(record.levelname)), 1)


class _ColoredFormatter(logging.Formatter):
    LEVELS: ClassVar[list[tuple[int, str]]] = [
        (logging.DEBUG, "\x1b[32m"),
        (logging.INFO, "\x1b[36;1m"),
        (logging.WARNING, "\x1b[33m"),
        (logging.ERROR, "\x1b[31;1m"),
        (logging.CRITICAL, "\x1b[41;1m"),
    ]

    FORMATTERS: ClassVar[dict[int, logging.Formatter]] = {
        level: logging.Formatter(
            f"\x1b[30m%(asctime)s\x1b[0m {color}[%(levelname)s]\x1b[0m BLANK"
            f"\x1b[35m%(name)s\x1b[0m: \x1b[97;1m%(message)s\x1b[0m",
            "%Y/%m/%d %H:%M:%S"
        ) for level, color in LEVELS
    }

    def format(self, record: logging.LogRecord) -> str:
        fmt = self.FORMATTERS.get(record.levelno)
        if fmt is None:
            fmt = self.FORMATTERS[logging.DEBUG]

        output = fmt.format(record)
        output = output.replace("BLANK", " " * (8 - len(record.levelname)), 1)
        record.exc_text = None
        return output


class _SettingsSentinel:
    __slots__ = (
        "__allow_global_uses",
        "__flag_delimiter",
        "__invoke_on_edit",
        "__locale",
        "__owners",
        "__path_to_file",
        "__root_folder",
        "__virtual_vars",
        "mapping",
        "kwargs"
    )

    def __init__(self, **kwargs: Any):
        self.__allow_global_uses: bool = kwargs.setdefault("allow_global_uses", False)
        self.__flag_delimiter: str = kwargs.setdefault("flag_delimiter", "=")
        self.__invoke_on_edit: bool = kwargs.setdefault("invoke_on_edit", False)
        self.__locale: str = kwargs.setdefault("locale", "en-US")
        self.__owners: set[int] = kwargs.setdefault("owners", set())
        self.__path_to_file: str = kwargs.setdefault("path_to_file", os.getcwd())
        self.__root_folder: str = kwargs.setdefault("root_folder", "")
        self.__virtual_vars: str = kwargs.setdefault("virtual_vars", "|%s|")
        self.kwargs: dict[str, Any] = kwargs
        self.mapping: dict[str, type[Any]] = {
            "allow_global_uses": bool,
            "flag_delimiter": str,
            "invoke_on_edit": bool,
            "owners": set,
            "path_to_file": str,
            "root_folder": str,
            "virtual_vars": str
        }

    @property
    def allow_global_uses(self) -> bool:
        """:class:`bool`:
        Commands that have their `global_use` property set True are allowed to be invoked by any user.
        Defaults to `False`.
        """
        return self.__allow_global_uses

    @allow_global_uses.setter
    def allow_global_uses(self, value: bool) -> None:
        self.__allow_global_uses = bool(value)
        self.kwargs["allow_global_uses"] = value

    @property
    def flag_delimiter(self) -> str:
        """:class:`str`:
        The characters that determines when to separate a key from its value when parsing strings to dictionaries.
        Defaults to `=`.
        """
        return self.__flag_delimiter

    @flag_delimiter.setter
    def flag_delimiter(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError(f"Expected type str, got {type(value)!r}")
        if value.strip() == ":":
            raise ValueError(f"Delimiter cannot be {value!r}")
        self.__flag_delimiter = value
        self.kwargs["flag_delimiter"] = value

    @property
    def invoke_on_edit(self) -> bool:
        """:class:`bool`:
        Whenever a message that invoked a command is edited to another command, the bot will try to invoke the new
        command.
        Defaults to `False`.
        """
        return self.__invoke_on_edit

    @invoke_on_edit.setter
    def invoke_on_edit(self, value: bool) -> None:
        self.__invoke_on_edit = bool(value)
        self.kwargs["invoke_on_edit"] = bool(value)

    @property
    def locale(self) -> str:
        """:class:`str`
        Locale that will be used whenever emulating a Discord object.
        Defaults to `en-US`.
        """
        return self.__locale

    @locale.setter
    def locale(self, value: str | discord.Locale) -> None:
        if isinstance(value, str):
            try:
                locale = discord.Locale(value)
            except KeyError as exc:
                raise ValueError("Invalid locale") from exc
            self.__locale = locale.value
        else:
            self.__locale = value.value  # noqa

    @property
    def owners(self) -> set[int]:
        """Set[:class:`int`]:
        A set of user IDs that override bot ownership IDs. If specified, users that are only found in the ownership ID
        list will not be able to use this extension.
        """
        return self.__owners

    @owners.setter
    def owners(self, value: set[int]) -> None:
        if not isinstance(value, set):
            value = set(value)
        self.__owners = value
        self.kwargs["owners"] = value

    @property
    def path_to_file(self) -> str:
        """:class:`str`:
        A path directory that will be removed if found inside a message. This will typically be used in tracebacks.
        Defaults to the current working directory. This must be a valid path.
        """
        return self.__path_to_file

    @path_to_file.setter
    def path_to_file(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError(f"Expected type str, got {type(value)!r}")
        _folder = pathlib.Path(value)
        if not _folder.exists() or not _folder.is_dir():
            raise NotADirectoryError(value)
        if not value.endswith("/"):
            value += "/"
        self.__path_to_file = value
        self.kwargs["path_to_file"] = value

    @property
    def root_folder(self) -> str:
        """:class:`str`:
        The path that will replace the `|root|` text placeholder. This must be a valid path.
        """
        return self.__root_folder

    @root_folder.setter
    def root_folder(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError(f"Expected type str, got {type(value)!r}")
        _folder = pathlib.Path(value)
        if not _folder.exists() or not _folder.is_dir():
            raise NotADirectoryError(value)
        self.__root_folder = value
        self.kwargs["root_folder"] = value

    @property
    def virtual_vars(self) -> str:
        """:class:`str`
        The format in which virtual variables are expected to be formatted. The actual place where the variable's name
        will be should be defined as `%s`.
        Defaults to `|%s|`.
        """
        return self.__virtual_vars

    @virtual_vars.setter
    def virtual_vars(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError(f"Expected type str, got {type(value)!r}")
        if value.count("%s") != 1:
            raise ValueError(f"Got 0 or more than 1 instance of '%s', exactly 1 expected")
        self.__virtual_vars = value
        self.kwargs["virtual_vars"] = value

    def copy(self) -> _SettingsSentinel:
        return _SettingsSentinel(**self.kwargs)

    def exists(self, setting_name: str, /) -> bool:
        return setting_name in self.mapping.keys()


Settings = _SettingsSentinel()


def setup_logging(
        *,
        level: int = logging.INFO,
        handler: logging.Handler = logging.StreamHandler(),
        formatter: logging.Formatter = MISSING
) -> logging.Logger:
    if formatter is MISSING:
        formatter = (
            _ColoredFormatter()
            if isinstance(handler, logging.StreamHandler) and stream_supports_colour(handler.stream)
            else _DefaultFormatter()
        )

    lib, _, _ = __name__.partition(".")
    logger = logging.getLogger(lib)
    #  Check if logging has already been set up
    if not logger.handlers:
        handler.setFormatter(formatter)
        logger.setLevel(level)
        logger.addHandler(handler)
    return logger


async def enforce_owner(bot: types.Bot) -> logging.Logger:
    _log = setup_logging()
    if not any((Settings.owners, bot.owner_ids, bot.owner_id)):
        #  Try to set the owner as the application's owner or its team members
        try:
            if bot.application.owner:  # type: ignore
                Settings.owners = {bot.application.owner.id}  # type: ignore
            elif bot.application.team:  # type: ignore
                Settings.owners = {owner.id for owner in bot.application.team.members}  # type: ignore
        except AttributeError:
            pass
        else:
            _log.warning(
                "No owners were set. Falling back to the owner of the application (%s).",
                ", ".join(map(str, Settings.owners))
            )
    if not any((Settings.owners, bot.owner_ids, bot.owner_id)):
        #  The application was not logged in when we tried to get the info, and no other owner IDs were set
        raise RuntimeError("For security reasons, an owner ID must be set")
    return _log
