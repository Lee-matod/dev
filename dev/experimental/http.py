# -*- coding: utf-8 -*-

"""
dev.experimental.http
~~~~~~~~~~~~~~~~~~~~~

HTTP requests and response evaluator.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import io
import json
from typing import TYPE_CHECKING, Literal

import aiohttp
import discord

from dev.converters import LiteralModes
from dev.handlers import replace_vars

from dev.utils.baseclass import Root, root
from dev.utils.functs import flag_parser, send
from dev.utils.startup import Settings
from dev.utils.utils import responses

if TYPE_CHECKING:
    from discord.ext import commands

    from dev import types


class RootHTTP(Root):

    @root.group(name="http", parent="dev", virtual_vars=True)
    async def root_http(
            self,
            ctx: commands.Context[types.Bot],
            url: str,
            mode: LiteralModes[Literal["json", "read", "status", "text"]],
            allow_redirects: bool = False,
            *,
            options: str | None = None
    ) -> discord.Message | None:
        """Send an HTTP request using GET method.
        **Modes:**
        `json` = Converts the response to JSON. This isn't always available.
        `read` = Read the response and return it.
        `status` = Return the status code of the website.
        `text` = Send the response as text.
        """
        if mode is None:
            return
        try:
            kwargs = flag_parser(replace_vars(options or '', Root.scope), Settings.FLAG_DELIMITER.strip())
        except json.JSONDecodeError as exc:
            return await send(ctx, f"{exc}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                        replace_vars(url, Root.scope),
                        allow_redirects=allow_redirects,
                        **kwargs
                ) as request:
                    if mode == "status":  # pyright: ignore [reportUnnecessaryComparison]
                        await send(
                            ctx,
                            discord.Embed(
                                title=f"Status {(status := str(request.status))}",
                                description=f"{(f'{t}.' if (t := responses.get(status[0])) else '')}"
                                            f"{f' ‒ {r}.' if (r := request.reason) else ''}".strip(),  # type: ignore
                                color=discord.Color.blurple(),
                                url=f"https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/{status}"
                            )
                        )
                    elif mode == "json":  # pyright: ignore [reportUnnecessaryComparison]
                        try:
                            json_dict = await request.json()
                            with io.BytesIO() as binary_file:
                                binary_file.write(json.dumps(json_dict, indent=2).encode("utf-8"))
                                binary_file.seek(0)
                                await send(ctx, discord.File(filename="response.json", fp=binary_file))
                        except json.JSONDecodeError:
                            await send(ctx, "Unable to decode to JSON.")
                    elif mode == "text":  # pyright: ignore [reportUnnecessaryComparison]
                        file = await request.text()
                        await send(ctx, discord.File(filename="response.txt", fp=io.BytesIO(file.encode("utf-8"))))
                    elif mode == "read":  # pyright: ignore [reportUnnecessaryComparison]
                        file = await request.read()
                        with io.BytesIO() as binary_file:
                            binary_file.write(file)
                            binary_file.seek(0)
                            await send(ctx, discord.File(filename="response", fp=binary_file))
            except aiohttp.InvalidURL:
                await send(ctx, "Invalid URL link.")
            except aiohttp.ClientConnectorError:
                await send(ctx, "Cannot connect to host. Name or service not known.")
