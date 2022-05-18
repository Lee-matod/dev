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
    "local_globals",
    "plural"
)

local_globals: Dict[Any, Any] = {}  # lmao


def escape(content: str):
    return escape_markdown(escape_mentions(content))


def plural(amount: int, singular: str) -> str:
    return f"{amount} {singular}" if amount == 1 else f"{amount} {singular}s" if not singular.endswith("s") else f"{amount} {singular}'"
