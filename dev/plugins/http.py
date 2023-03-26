# -*- coding: utf-8 -*-

"""
dev.plugins.http
~~~~~~~~~~~~~~~~

HTTP requests and response evaluator.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import io
import json
from typing import TYPE_CHECKING, Literal

import aiohttp
import discord

from dev import root
from dev.handlers import replace_vars
from dev.utils.functs import flag_parser, send
from dev.utils.startup import Settings
from dev.utils.utils import responses

if TYPE_CHECKING:
    from discord.ext import commands

    from dev import types

CONTENT_TYPES: dict[str, str] = {
    "application/zip": "zip",
    "application/xml": "xml",
    "application/json": "json",
    "application/ogg": "ogg",
    "application/pdf": "pdf",
    "application/xhtml+xml": "xhtml",
    "application/javascript": "js",
    "image/gif": "gif",
    "image/jpeg": "jpeg",
    "image/png": "png",
    "text/css": "css",
    "text/csv": "csv",
    "text/html": "html",
    "text/javascript": "js",
    "text/xml": "xml",
    "video/mp4": "mp4",
    "video/webm": "webm",
}


class RootHTTP(root.Plugin):
    """HTTP request commands"""

    @root.group("http", parent="dev", virtual_vars=True)
    async def root_http(
        self,
        ctx: commands.Context[types.Bot],
        url: str,
        mode: Literal["json", "read", "status"],
        allow_redirects: bool = False,
        *,
        options: str | None = None,
    ):
        """Send an HTTP GET request to *url*.
        *options* should be written in valid JSON format.
        **Modes:**
        `json` = Converts the response to JSON. This isn't always available.
        `read` = Read the response and return it.
        `status` = Return the status code of the website.
        """
        #  Perhaps '>' is a needed literal in a parameter, so we shouldn't remove it
        #  if not necessary
        if url.startswith("<") and url.endswith(">"):
            url = url[1:-1]
        try:
            kwargs = flag_parser(replace_vars(options or "", self.scope), Settings.flag_delimiter.strip())
        except json.JSONDecodeError as exc:
            return await send(ctx, f"Parsing options failed. {exc}")
        async with aiohttp.ClientSession() as session:
            try:
                request = await session.get(replace_vars(url, self.scope), allow_redirects=allow_redirects, **kwargs)
            except aiohttp.InvalidURL:
                return await send(ctx, "Invalid URL link.")
            except aiohttp.ClientConnectorError:
                return await send(ctx, "Cannot connect to host. Name or service not known.")
            if mode == "status":
                status = str(request.status)
                status_type = responses[status[0]]
                colors = {
                    "1": discord.Color.light_grey(),
                    "2": discord.Color.green(),
                    "3": discord.Color.gold(),
                    "4": discord.Color.red(),
                    "5": discord.Color.dark_red(),
                }
                await send(
                    ctx,
                    discord.Embed(
                        title=f"Status {status}",
                        description=f"{status_type} ‒ {request.reason}".strip(),  # type: ignore
                        color=colors[status[0]],
                        url=f"https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/{status}",
                    ),
                )
            elif mode == "json":
                try:
                    js = await request.json()
                except (json.JSONDecodeError, aiohttp.ContentTypeError):
                    return await send(ctx, "Unable to decode to JSON.")
                with io.BytesIO() as binary_file:
                    binary_file.write(json.dumps(js, indent=2).encode("utf-8"))
                    binary_file.seek(0)
                    await send(ctx, discord.File(filename="response.json", fp=binary_file))
            elif mode == "read":
                data = await request.read()
                if not data:
                    return await send(ctx, "Response was empty.")
                file_ext = CONTENT_TYPES.get(request.content_type, "txt")
                with io.BytesIO() as binary_file:
                    binary_file.write(data)
                    binary_file.seek(0)
                    await send(ctx, discord.File(filename=f"response.{file_ext}", fp=binary_file))
