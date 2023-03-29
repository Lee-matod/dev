# -*- coding: utf-8 -*-

"""
dev.utils.startup
~~~~~~~~~~~~~~~~~

Extension loading function and settings checker.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

from discord.utils import MISSING, stream_supports_colour

from dev.scope import Settings

if TYPE_CHECKING:
    from dev import types

__all__ = ("enforce_owner", "setup_logging")


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
            f"\x1b[35m%(name)s:\x1b[0m \x1b[97;1m%(message)s\x1b[0m",
            "%Y/%m/%d %H:%M:%S",
        )
        for level, color in LEVELS
    }

    def format(self, record: logging.LogRecord) -> str:
        fmt = self.FORMATTERS.get(record.levelno)
        if fmt is None:
            fmt = self.FORMATTERS[logging.DEBUG]

        output = fmt.format(record)
        output = output.replace("BLANK", " " * (8 - len(record.levelname)), 1)
        record.exc_text = None
        return output


def setup_logging(
    *, level: int = logging.INFO, handler: logging.Handler = MISSING, formatter: logging.Formatter = MISSING
) -> logging.Logger:
    if handler is MISSING:
        handler = logging.StreamHandler()

    if formatter is MISSING:
        formatter = (
            _ColoredFormatter()
            if isinstance(handler, logging.StreamHandler) and stream_supports_colour(handler.stream)  # type: ignore
            else _DefaultFormatter()
        )

    lib, _, _ = __name__.partition(".")
    logger = logging.getLogger(lib)
    #  Check if logging has already been set up
    if not logger.handlers:
        handler.setFormatter(formatter)
        logger.setLevel(level)
        logger.addHandler(handler)  # type: ignore
    return logger


async def enforce_owner(bot: types.Bot) -> logging.Logger:
    _log = setup_logging()
    if not any((Settings.OWNERS, bot.owner_ids, bot.owner_id)):
        #  Try to set the owner as the application's owner or its team members
        try:
            if bot.application.owner:  # type: ignore
                Settings.OWNERS = {bot.application.owner.id}  # type: ignore
            elif bot.application.team:  # type: ignore
                Settings.OWNERS = {owner.id for owner in bot.application.team.members}  # type: ignore
        except AttributeError:
            pass
        else:
            _log.warning(
                "No owners were set. Falling back to the owner of the application (%s).",
                ", ".join(map(str, Settings.OWNERS)),
            )
    if not any((Settings.OWNERS, bot.owner_ids, bot.owner_id)):
        #  The application was not logged in when we tried to get the info,
        #  and no other owner IDs were set
        raise RuntimeError("For security reasons, an owner ID must be set")
    return _log
