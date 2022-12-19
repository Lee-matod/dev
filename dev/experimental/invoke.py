# -*- coding: utf-8 -*-

"""
dev.experimental.invoke
~~~~~~~~~~~~~~~~~~~~~~~

Command invocation or reinvocation with changeable execution attributes.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import discord
from discord.ext import commands

from dev.handlers import ExceptionHandler, TimedInfo
from dev.types import Invokeable

from dev.utils.baseclass import Root, root
from dev.utils.functs import generate_ctx, send
from dev.utils.interaction import SyntheticInteraction, get_app_command
from dev.utils.startup import Settings

if TYPE_CHECKING:
    from dev import types


class RootInvoke(Root):

    @root.command(name="timeit", parent="dev", require_var_positional=True)
    async def root_timeit(
            self,
            ctx: commands.Context[types.Bot],
            timeout: float | None,
            *,
            command_string: str
    ) -> discord.Message | None:
        """Invoke a command and measure how long it takes to invoke finish.
        Optionally add a maximum amount of time that the command can take to finish executing.
        """
        kwargs = {"content": f"{ctx.prefix}{command_string}"}
        invokable = await self.get_invokable(ctx, command_string, kwargs)
        if invokable is None:
            return await send(ctx, f"Command `{command_string}` not found.")
        command, context = invokable

        info = TimedInfo(timeout=timeout)
        if timeout is not None:
            self.bot.loop.create_task(info.wait_for(ctx.message))
        info.start = time.perf_counter()
        await command.invoke(context)
        info.end = time.perf_counter()
        await send(ctx, f"Command finished in {info.end - info.start:.3f}s.", forced=True)

    @root.command(name="repeat", parent="dev", aliases=["repeat!"], require_var_positional=True)
    async def root_repeat(
            self,
            ctx: commands.Context[types.Bot],
            amount: int,
            *,
            command_string: str
    ) -> discord.Message | None:
        """Call a command a given amount of times.
        Checks can be optionally bypassed by using `dev repeat!` instead of `dev repeat`.
        """
        kwargs = {"content": f"{ctx.prefix}{command_string}"}
        assert ctx.invoked_with is not None
        for _ in range(amount):
            invokable = await self.get_invokable(ctx, command_string, kwargs)
            if invokable is None:
                return await send(ctx, f"Command `{command_string}` not found.")
            command, context = invokable
            if ctx.invoked_with.endswith("!"):
                await command.reinvoke(context)
            else:
                await command.invoke(context)

    @root.command(name="debug", parent="dev", aliases=["dbg"], require_var_positional=True)
    async def root_debug(self, ctx: commands.Context[types.Bot], *, command_string: str) -> discord.Message | None:
        """Catch errors when executing a command.
        This command will probably not work with commands that already have an error handler.
        """
        kwargs = {"content": f"{ctx.prefix}{command_string}"}
        invokable = await self.get_invokable(ctx, command_string, kwargs)
        if invokable is None:
            return await send(ctx, f"Command `{command_string}` not found.")
        command, context = invokable
        async with ExceptionHandler(ctx.message, save_traceback=True) as handler:
            await command.invoke(context)
        if handler.error:
            embeds = [
                discord.Embed(
                    title=exc[0],
                    description=f"```py\n{exc[1].replace(Settings.PATH_TO_FILE, '')}\n```",
                    color=discord.Color.red()
                )
                for exc in handler.error]
            handler.cleanup()
            await send(ctx, embeds)
        else:
            await ctx.message.add_reaction("☑")

    @root.command(name="execute", parent="dev", aliases=["exec", "execute!", "exec!"], require_var_positional=True)
    async def root_execute(
            self,
            ctx: commands.Context[types.Bot],
            attrs: commands.Greedy[
                discord.Member | discord.TextChannel | discord.Thread | discord.Role
            ],
            *,
            command_attr: str
    ) -> discord.Message | None:
        """Execute a command with custom attributes.
        Attribute support types are `discord.Member`, `discord.Role`, `discord.TextChannel` and `discord.Thread`.
        These will override the current context, thus executing the command in a different virtual environment.
        Command checks can be optionally disabled by adding an exclamation mark at the end of the `execute` command.
        """
        kwargs: dict[str, Any] = {"content": f"{ctx.prefix}{command_attr}"}
        roles: list[int] = []
        for attr in attrs:
            if isinstance(attr, discord.Member):
                kwargs["author"] = attr
            elif isinstance(attr, (discord.TextChannel, discord.Thread)):
                kwargs["channel"] = attr
            elif isinstance(attr, discord.Role):  # pyright: ignore [reportUnnecessaryIsInstance]
                kwargs["author"]._roles.add(attr.id)  # pyright: ignore [reportPrivateUsage]
                roles.append(attr.id)
        assert ctx.invoked_with is not None
        invokable = await self.get_invokable(ctx, command_attr, kwargs)
        try:
            if invokable is None:
                return await send(ctx, f"Command `{command_attr}` not found.")
            command, context = invokable
            if ctx.invoked_with.endswith("!"):
                return await command.reinvoke(context)
            return await command.invoke(context)
        finally:
            for role in roles:
                del kwargs["author"]._roles[role]  # pyright: ignore [reportPrivateUsage]

    async def get_invokable(
            self,
            ctx: commands.Context[types.Bot],
            content: str,
            kwargs: dict[str, Any]
    ) -> tuple[Invokeable, commands.Context[types.Bot]] | None:
        if content.startswith("/"):
            app_commands = self.bot.tree.get_commands(type=discord.AppCommandType.chat_input)
            app_command = get_app_command(command_attr.removeprefix("/"), app_commands.copy())  # type: ignore
            if app_command is None:
                return
            kwargs["content"] = kwargs["content"].removeprefix(ctx.prefix)
            context = await generate_ctx(ctx, **kwargs)
            return SyntheticInteraction(context, app_command), context
        context = await generate_ctx(ctx, **kwargs)
        if context.command is not None:
            return context.command, context
