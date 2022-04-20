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

from dev.utils.baseclass import root
from dev.utils.startup import settings
from dev.utils.functs import is_owner, send
from dev.handlers import VirtualVarReplacer


class RootHTTP(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @root.command(name="http", parent="dev", version=1.2, supports_virtual_vars=True)
    @is_owner()
    async def root_http(self, ctx: commands.Context, url: str, mode: str, allow_redirects: bool = False):
        """Get a response from a specified url. Response modes can differ.
        **Modes:**
        `status` = Return the status code of the website.
        `json` = Convert the response to JSON. This isn't always available.
        `text` = Send the response as text.
        `read` = Read the response and return it.
        """
        async with aiohttp.ClientSession() as SESSION:
            with VirtualVarReplacer(settings, url) as decoded_url:
                try:
                    async with SESSION.get(decoded_url, allow_redirects=allow_redirects) as request:
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


async def setup(bot):
    await bot.add_cog(RootHTTP(bot))