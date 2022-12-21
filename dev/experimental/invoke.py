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
from typing import TYPE_CHECKING, Any, Union

import discord
from discord.ext import commands

from dev.converters import GlobalTextChannelConverter
from dev.handlers import ExceptionHandler, TimedInfo
from dev.types import Invokeable

from dev.utils.baseclass import Root, root
from dev.utils.functs import generate_ctx, send
from dev.utils.interaction import SyntheticInteraction, get_app_command

if TYPE_CHECKING:
    from dev import types


_DiscordObjects = Union[GlobalTextChannelConverter, discord.Guild, discord.Member, discord.Thread, discord.User]



class RootInvoke(Root):

    @root.command(name="timeit", parent="dev", require_var_positional=True)
    async def root_timeit(
            self,
            ctx: commands.Context[types.Bot],
            timeout: float | None,
            *,
            command_string: str
    ):
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
    ):
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
    async def root_debug(self, ctx: commands.Context[types.Bot], *, command_string: str):
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
                    description=f"```py\n{exc[1]}\n```",
                    color=discord.Color.red()
                )
                for exc in handler.error]
            handler.cleanup()
            await send(ctx, embeds)
        else:
            await ctx.message.add_reaction("\u2611")

    @root.command(name="execute", parent="dev", aliases=["exec", "execute!", "exec!"], require_var_positional=True)
    async def root_execute(
            self,
            ctx: commands.Context[types.Bot],
            attrs: commands.Greedy[_DiscordObjects],
            *,
            command_attr: str
    ):
        """Execute a command with custom attributes.
        Attribute support types are `discord.Member`, `discord.Guild`, `discord.TextChannel` and `discord.Thread`.
        These will override the current context, thus executing the command in a different virtual environment.
        Command checks can be optionally disabled by adding an exclamation mark at the end of the `execute` command.
        """
        kwargs: dict[str, Any] = {"content": f"{ctx.prefix}{command_attr}"}
        for attr in attrs:
            if isinstance(attr, (discord.User, discord.Member)):
                kwargs["author"] = attr
            elif isinstance(attr, discord.Guild):
                kwargs["guild"] = attr
            elif isinstance(attr, (discord.TextChannel, discord.Thread)):
                kwargs["channel"] = attr
        #  Try to upgrade to a Member using the given guild
        guild: discord.Guild | None = kwargs.get("guild")
        author: discord.User | None = kwargs.get("author")
        if guild is not None and author is not None:
            kwargs["author"] = guild.get_member(author.id) or author
        elif guild is None and author is not None and ctx.guild is not None:
            kwargs["author"] = ctx.guild.get_member(author.id) or author

        assert ctx.invoked_with is not None
        invokable = await self.get_invokable(ctx, command_attr, kwargs)
        if invokable is None:
            return await send(ctx, f"Command `{command_attr}` not found.")
        command, context = invokable
        if ctx.invoked_with.endswith("!"):
            return await command.reinvoke(context)
        return await command.invoke(context)

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
