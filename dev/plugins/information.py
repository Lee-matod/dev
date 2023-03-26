# -*- coding: utf-8 -*-

"""
dev.plugins.information
~~~~~~~~~~~~~~~~~~~~~~~

Command information features.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from dev import root
from dev.utils.functs import send
from dev.utils.utils import codeblock_wrapper, escape

if TYPE_CHECKING:
    from dev import types


class RootInformation(root.Plugin):
    """Inspection commands"""

    @root.command("inspect", parent="dev", global_use=True, require_var_positional=True)
    async def root_inspect(self, ctx: commands.Context[types.Bot], *, command_string: str):
        """Inspect a command.
        Receive command signature, aliases, and some other useful information.
        """
        command = self.bot.get_command(command_string)
        if not command:
            return await send(ctx, f"Command `{command_string}` not found.")
        params: list[str] = []
        for name, param in command.clean_params.items():
            fmt = ""
            if param.kind is inspect.Parameter.KEYWORD_ONLY:
                fmt += r"\*, `"
            elif param.kind is inspect.Parameter.VAR_POSITIONAL:
                fmt += r"`\*"
            else:
                fmt += "`"
            fmt += f"{name}"
            if param.required:
                fmt += "*"
            fmt += f"`: {escape(repr(param.converter))}"
            if param.default is not inspect.Parameter.empty:
                fmt += f" = {escape(str(getattr(param.default, '__name__', param.default)))}"
            params.append(fmt)

        embed = discord.Embed(
            title=command.qualified_name,
            description=escape(command.description) or None,
            color=discord.Color.darker_gray(),
        )
        if command.aliases:
            embed.add_field(name="Aliases", value=f"`{'`, `'.join(map(escape, command.aliases))}`")
        if command.cog:
            embed.add_field(name="Cog", value=f"`{command.cog_name}`")
        embed.add_field(name="Enabled", value=f"`{command.enabled}`")
        embed.add_field(name="Hidden", value=f"`{command.hidden}`")
        embed.add_field(name="Module", value=f"`{command.module}`")
        embed.add_field(name="Type", value=f"`{type(command).__name__}`")
        if command.extras:
            embed.add_field(name="Extras", value=", ".join(command.extras))
        if params:
            embed.add_field(name="Signature", value=", ".join(params), inline=False)
        embed.set_footer(text=f"{hex(id(command))}")
        await send(ctx, embed)

    @root.command("source", parent="dev", aliases=["src"], require_var_positional=True)
    async def root_source(self, ctx: commands.Context[types.Bot], *, command_string: str):
        """View the source code of a command.
        The token of the bot will be hidden as `[token]` if it is found within the source code.
        """
        command = self.bot.get_command(command_string)
        if not command:
            return await send(ctx, f"Command `{command_string}` not found.")

        over = self.get_last_implementation(command.qualified_name)
        if over is None or not over.source:
            try:
                source = inspect.getsource(command.callback)
            except OSError:
                return await send(ctx, f"Couldn't get source lines for the command `{command_string}`.")
            self._refresh_base_registrations()
        else:
            source = over.source
        return await send(ctx, codeblock_wrapper(source, "py"))
