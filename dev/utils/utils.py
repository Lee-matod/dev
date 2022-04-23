# -*- coding: utf-8 -*-

"""
dev.utils.utils
~~~~~~~~~~~~~~~

Basic utilities that will be used with the dev extension.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""

from typing import Any, Dict
from discord.utils import escape_markdown, escape_mentions

__all__ = (
    "escape",
    "MISSING",
    "local_globals"
)


class _MISSING:
    def __gt__(self, other):
        return False

    def __ge__(self, other):
        return False

    def __eq__(self, other):
        return False

    def __le__(self, other):
        return False

    def __lt__(self, other):
        return False

    def __repr__(self):
        return "..."

    def __hash__(self):
        return 0

    def __bool__(self):
        return False


MISSING = _MISSING()

local_globals: Dict[Any, Any] = {}


def escape(content: str):
    return escape_markdown(escape_mentions(content))
