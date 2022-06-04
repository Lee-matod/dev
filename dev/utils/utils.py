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
    "clean_code",
    "escape",
    "local_globals",
    "plural"
)

local_globals: Dict[Any, Any] = {}  # lmao


def clean_code(content: str) -> str:
    if content.startswith("```") and content.endswith("```"):
        return "\n".join(content.split("\n")[1:-1])
    else:
        return content


def escape(content: str):
    return escape_markdown(escape_mentions(content))


def plural(amount: int, singular: str, include_amount: bool = True) -> str:
    _plural = singular + ("s" if not singular.endswith("s") else "'")
    if singular == "is":
        _plural = "are"
    return f"{amount if include_amount else ''} {singular}".strip() if amount == 1 else f"{amount if include_amount else ''} {_plural}".strip()
