# -*- coding: utf-8 -*-

"""
dev.experimental.http
~~~~~~~~~~~~~~~~~~~~~

HTTP requests and response evaluator.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""

import io
import json
import aiohttp
import discord

from discord.ext import commands

from dev.handlers import replace_vars

from dev.utils.functs import send
from dev.utils.startup import Settings
from dev.utils.baseclass import root, Root


class RootHTTP(Root):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)

    @root.command(name="http", parent="dev", supports_virtual_vars=True)
    async def root_http(self, ctx: commands.Context, url: str, mode: str, allow_redirects: bool = False):
        """Get a response from a specified url. Response modes can differ.
        **Modes:**
        `status` = Return the status code of the website.
        `json` = Convert the response to JSON. This isn't always available.
        `text` = Send the response as text.
        `read` = Read the response and return it.
        """
        async with aiohttp.ClientSession() as SESSION:
            try:
                async with SESSION.get(replace_vars(url), allow_redirects=allow_redirects) as request:
                    if mode == "status":
                        await send(ctx, f"Response **{request.status}**")
                    elif mode == "json":
                        try:
                            file = await request.json()
                            await send(ctx, file=discord.File(filename="response.json", fp=io.BytesIO(file.encode("utf-8"))))
                        except json.JSONDecodeError:
                            await send(ctx, "Unable to decode to JSON.")
                    elif mode == "text":
                        file = await request.text()
                        await send(ctx, file=discord.File(filename="response.txt", fp=io.BytesIO(file.encode("utf-8"))))
                    elif mode == "read":
                        file = await request.read()
                        with io.BytesIO() as binary_file:
                            binary_file.write(file)
                            binary_file.seek(0)
                            await send(ctx, file=discord.File(filename="response", fp=binary_file))
            except aiohttp.InvalidURL:
                await send(ctx, "Invalid URL link.")