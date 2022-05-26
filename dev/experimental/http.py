# -*- coding: utf-8 -*-

"""
dev.experimental.http
~~~~~~~~~~~~~~~~~~~~~

HTTP requests and response evaluator.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""


import aiohttp
import discord
import io
import json

from discord.ext import commands
from typing import Dict, Literal

from dev.converters import LiteralModes
from dev.handlers import replace_vars

from dev.utils.baseclass import Root, root
from dev.utils.functs import send
from dev.utils.startup import Settings


class RootHTTP(Root):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)

    @root.command(name="http", parent="dev", virtual_vars=True)
    async def root_http(self, ctx: commands.Context, url: str, mode: LiteralModes[Literal["status", "json", "text", "read"]], allow_redirects: bool = False, *, options: str = None):
        """Get a response from a specified url. Response modes can differ.
        **Modes:**
        `status` = Return the status code of the website.
        `json` = Convert the response to JSON. This isn't always available.
        `text` = Send the response as text.
        `read` = Read the response and return it.
        """
        if mode is None:
            return
        kwargs = self.flag_parser(replace_vars(options or ''))
        async with aiohttp.ClientSession() as SESSION:
            try:
                async with SESSION.get(replace_vars(url), allow_redirects=allow_redirects, **kwargs) as request:
                    if mode == "status":
                        await send(ctx, f"Response **{request.status}**")
                    elif mode == "json":
                        try:
                            file = await request.json()
                            await send(ctx, discord.File(filename="response.json", fp=io.BytesIO(file.encode("utf-8"))))
                        except json.JSONDecodeError:
                            await send(ctx, "Unable to decode to JSON.")
                    elif mode == "text":
                        file = await request.text()
                        await send(ctx, discord.File(filename="response.txt", fp=io.BytesIO(file.encode("utf-8"))))
                    elif mode == "read":
                        file = await request.read()
                        with io.BytesIO() as binary_file:
                            binary_file.write(file)
                            binary_file.seek(0)
                            await send(ctx, discord.File(filename="response", fp=binary_file))
            except aiohttp.InvalidURL:
                await send(ctx, "Invalid URL link.")

    @staticmethod
    def flag_parser(string: str) -> Dict[str, str]:
        flags: Dict[str, str] = {}
        keys = []
        values = []
        temp_value = []
        searching_for_value = False
        for word in string.split():
            if word.endswith(Settings.FLAG_DELIMITER.strip()) and not temp_value:
                keys.append(word.removesuffix(Settings.FLAG_DELIMITER.strip()))
                searching_for_value = True
            if word.endswith(Settings.FLAG_DELIMITER.strip()) and temp_value:
                values.append(" ".join(temp_value))
                temp_value.clear()
                keys.append(word.removesuffix(Settings.FLAG_DELIMITER.strip()))
            elif searching_for_value:
                if not word.endswith(Settings.FLAG_DELIMITER.strip()):
                    temp_value.append(word)
        if temp_value:  # clear any temporary values that didn't get assigned to their keys
            values.append(" ".join(temp_value))

        for i in range(len(keys)):
            flags[keys[i]] = values[i]
        return flags
