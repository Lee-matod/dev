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

from discord.utils import MISSING, _ColourFormatter, stream_supports_colour

__all__ = ("setup_logging",)


def setup_logging(
    *, level: int = logging.INFO, handler: logging.Handler = MISSING, formatter: logging.Formatter = MISSING
) -> logging.Logger:
    if handler is MISSING:
        handler = logging.StreamHandler()

    if formatter is MISSING:
        formatter = (
            _ColourFormatter()
            if isinstance(handler, logging.StreamHandler) and stream_supports_colour(handler.stream)  # type: ignore
            else logging.Formatter("[{asctime}] [{levelname:<8}] {name}: {message}", "%Y-%m-%d %H:%M:%S", style="{")
        )

    lib, _, _ = __name__.partition(".")
    logger = logging.getLogger(lib)
    # Check if logging has already been set up
    if not logger.handlers:
        handler.setFormatter(formatter)
        logger.setLevel(level)
        logger.addHandler(handler)  # type: ignore
    return logger
