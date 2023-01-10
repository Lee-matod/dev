# -*- coding: utf-8 -*-

"""
dev.utils.utils
~~~~~~~~~~~~~~~

Basic utilities used within the dev extension.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

from typing import TYPE_CHECKING
from discord.utils import escape_markdown, escape_mentions

if TYPE_CHECKING:
    from discord.ext import commands

    from dev import types

__all__ = (
    "clean_code",
    "codeblock_wrapper",
    "escape",
    "plural",
    "responses"
)

responses: dict[str, str] = {
    "1": "Informational response",
    "2": "Successful response",
    "3": "Redirection response",
    "4": "Client error response",
    "5": "Server error response"
}


def parse_invoked_subcommand(context: commands.Context[types.Bot], /) -> str:
    assert context.prefix is not None and context.command is not None
    command = context.prefix + context.command.qualified_name
    invoked = context.message.content.removeprefix(command).strip()
    if not invoked:
        return invoked
    return invoked.split()[0]


def clean_code(content: str) -> str:
    """Removes any leading and trailing backticks from a string.

    Parameters
    ----------
    content: :class:`str`
        The string that should be parsed.

    Returns
    -------
    str
      The cleaned up string without any leading or trailing backticks.
    """
    if content.startswith("```") and content.endswith("```"):
        content = "\n".join(content.split("\n")[1:])
        return "\n".join(content.split("\n")[:-1]) if content.split("\n")[-1] == "```" else content[:-3]
    return content


def codeblock_wrapper(content: str, highlight_language: str = "", /) -> str:
    """Add leading and trailing backticks to the given string.

    You can optionally add a highlight language, as well as change the highlight language
    if `content` were to be wrapped in backticks.

    See Also
    --------
    https://highlightjs.org/

    Parameters
    ----------
    content: :class:`str`
        The string that should get wrapped inside backticks.
    highlight_language: :class:`str`
        The highlight language that should be used.

    Returns
    -------
    str
        The parsed codeblock.
    """
    if content.startswith("```") and content.endswith("```"):
        new_content = "\n".join(content.split("\n")[1:])
        return f"```{highlight_language}\n{new_content}"
    return f"```{highlight_language}\n{content}\n```"


def escape(content: str) -> str:
    """A helper function that combines both :meth:`discord.utils.escape_markdown`
    and :meth:`discord.utils.escape_mentions`

    Parameters
    ----------
    content: :class:`str`
        The string that should be escaped.

    Returns
    -------
    str
        The cleaned up string without any markdowns or mentions.
    """
    return escape_markdown(escape_mentions(content))


def plural(amount: int, singular: str, include_amount: bool = True) -> str:
    """A helper function that returns a plural form of the word given if the amount isn't 1 (one).

    Parameters
    ----------
    amount: :class:`int`
        The amount of things that should be taken into consideration.
    singular: :class:`str`
        The singular form of the word.
    include_amount: :class:`bool`
        Whether to return a string with the included amount.

    Returns
    -------
    str
        The formatted string with its plural/singular form.
    """
    _plural = singular + ("s" if not singular.endswith("s") else "'")
    if singular == "is":
        _plural = "are"
    return f"{amount if include_amount else ''} {singular}".strip() if amount == 1 else \
        f"{amount if include_amount else ''} {_plural}".strip()
