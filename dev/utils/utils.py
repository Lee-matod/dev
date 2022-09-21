# -*- coding: utf-8 -*-

"""
dev.utils.utils
~~~~~~~~~~~~~~~

Basic utilities used within the dev extension.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from typing import Dict

from discord.utils import escape_markdown, escape_mentions


__all__ = (
    "clean_code",
    "codeblock_wrapper",
    "escape",
    "plural",
    "responses"
)


responses: Dict[str, str] = {
    "1": "Informational response",
    "2": "Successful response",
    "3": "Redirection response",
    "4": "Client error response",
    "5": "Server error response",
    "100": "Continue",
    "101": "Switching Protocols",
    "102": "Processing",
    "103": "Early Hints",
    "200": "OK",
    "201": "Created",
    "202": "Accepted",
    "203": "Non-Authoritative Information",
    "204": "No Content",
    "205": "Reset Content",
    "206": "Partial Content",
    "207": "Multi-Status",
    "208": "Already Reported",
    "226": "IM Used",
    "300": "Multiple Choices",
    "301": "Moved Permanently",
    "302": "Found",
    "303": "See Other",
    "304": "Not Modified",
    "305": "Use Proxy",
    "307": "Temporary Redirect",
    "308": "Permanent Redirect",
    "400": "Bad Request",
    "401": "Unauthorized",
    "402": "Payment Required",
    "403": "Forbidden",
    "404": "Not Found",
    "405": "Method Not Allowed",
    "406": "Not Acceptable",
    "407": "Proxy Authentication Required",
    "408": "Request Timeout",
    "409": "Conflict",
    "410": "Gone",
    "411": "Length Required",
    "412": "Precondition Failed",
    "413": "Payload Too Large",
    "414": "URL Too Long",
    "415": "Unsupported Media Type",
    "416": "Range Not Satisfiable",
    "417": "Expectation Failed",
    "418": "I'm a teapot",
    "421": "Misdirected Request",
    "422": "Unprocessable Entity",
    "423": "Locked",
    "424": "Failed Dependency",
    "425": "Too Early",
    "426": "Upgrade Required",
    "428": "Precondition Required",
    "429": "Too Many Requests",
    "431": "Request Header Fields Too Large",
    "451": "Unavailable For Legal Reasons",
    "500": "Internal Server Error",
    "501": "Not Implemented",
    "502": "Bad Gateway",
    "503": "Service Unavailable",
    "504": "Gateway Timeout",
    "505": "HTTP Version Not Supported",
    "506": "Variant Also Negotiates",
    "507": "Insufficient Storage",
    "508": "Loop Detected",
    "510": "Not Extended",
    "511": "Network Authentication Required"
}


def clean_code(content: str) -> str:
    """Removes any leading and trailing backticks from a string.

    Technically speaking, this just removes the first and last line of
    the string that was passed if it starts with and ends with 3 (three)
    backticks.

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
    else:
        return content


def codeblock_wrapper(content: str, highlight_language: str = "") -> str:
    """Opposite of :func:`clean_code`. Instead or removing any leading and trailing backticks, it adds them.

    You can optionally add a highlight language, as well as change the highlight language
    if `content` were to be wrapped in backticks.

    See Also
    --------
    https://highlightjs.org/ a list of supported highlights that Discord uses.

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
