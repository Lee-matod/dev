# -*- coding: utf-8 -*-

"""
dev.plugins.invoke
~~~~~~~~~~~~~~~~~~

Alterable command invocations.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Tuple, Union

import discord
from discord.ext import commands

from dev import root
from dev.converters import GlobalTextChannelConverter
from dev.handlers import ExceptionHandler, TimedInfo
from dev.interactions import SyntheticInteraction, get_app_command, get_parameters
from dev.types import Annotated
from dev.utils.functs import generate_ctx, send

if TYPE_CHECKING:
    from dev import types

_DiscordObjects = Union[GlobalTextChannelConverter, discord.Guild, discord.Member, discord.Thread, discord.User]


class RootInvoke(root.Plugin):
    """Invoke commands with some additional diagnostics and debugging abilities."""

    @root.command("timeit", parent="dev", require_var_positional=True)
    async def root_timeit(self, ctx: commands.Context[types.Bot], timeout: Optional[float], *, command_name: str):
        """Invoke a command and measure how long it takes to finish.

        If a timeout is set, the command's invocation will not be canceled.

        Parameters
        ----------
        timeout: Optional[:class:`float`]
            A maximum amount of time that the command is allowed to take to finish executing.
        command_name: :class:`str`
            The name of the command to invoke.
        """
        kwargs = {"content": f"{ctx.prefix}{command_name}"}
        invokable = await self._get_invokable(ctx, command_name, kwargs)
        if invokable is None:
            return await send(ctx, f"Command `{command_name}` not found.")

        timeit = TimedInfo(timeout=timeout)
        if timeout is not None:
            self.bot.loop.create_task(timeit.wait_for(ctx.message.reply("Command timed out.", mention_author=False)))
        with timeit:
            await self._execute_invokable(*invokable)
        await send(ctx, f"Command finished in {timeit.duration:.3f}s ({timeit}).", forced=True)

    @root.command("repeat", parent="dev", aliases=["repeat!"], require_var_positional=True)
    async def root_repeat(self, ctx: commands.Context[types.Bot], amount: int, *, command_name: str):
        """Repeatedly call a command a given amount of times.

        Checks can be optionally bypassed by using `dev repeat!` instead of `dev repeat`.

        Parameters
        ----------
        amount: :class:`int`
            How many times the command should be invoked.
        command_name: :class:`str`
            The qualified name of the command to invoke.
        """
        kwargs = {"content": f"{ctx.prefix}{command_name}"}
        assert ctx.invoked_with is not None
        for _ in range(amount):
            invokable = await self._get_invokable(ctx, command_name, kwargs)
            if invokable is None:
                return await send(ctx, f"Command `{command_name}` not found.")
            args = (*invokable, "reinvoke" if ctx.invoked_with.endswith("!") else "invoke")
            await self._execute_invokable(*args)

    @root.command("debug", parent="dev", aliases=["dbg"], require_var_positional=True)
    async def root_debug(self, ctx: commands.Context[types.Bot], *, command_name: str):
        """Catch any errors when executing a command and send the traceback.

        Parameters
        ----------
        command_name: :class:`str`
            The qualified name of the command to invoke.
        """
        kwargs = {"content": f"{ctx.prefix}{command_name}"}
        invokable = await self._get_invokable(ctx, command_name, kwargs)
        if invokable is None:
            return await send(ctx, f"Command `{command_name}` not found.")
        async with ExceptionHandler(ctx.message, save_traceback=True) as handler:
            await self._execute_invokable(*invokable)
        if handler.error:
            embeds = [
                discord.Embed(title=exc[0], description=f"```py\n{exc[1]}\n```", color=discord.Color.red())
                for exc in handler.error
            ]
            handler.cleanup()
            await send(ctx, embeds)
        else:
            await ctx.message.add_reaction("\u2611")

    @root.command("execute", parent="dev", aliases=["exec", "execute!", "exec!"], require_var_positional=True)
    async def root_execute(
        self,
        ctx: commands.Context[types.Bot],
        attrs: Annotated[List[_DiscordObjects], commands.Greedy[_DiscordObjects]],
        *,
        command_name: str,
    ):
        """Execute a command in a custom environment.

        Supported additional attributes are Member, Guild, TextChannel, and Thread.
        Command checks can be optionally disabled by using `dev exec!|execute!` instead.

        Application command invocation is also supported. Prefix the command name with a slash to invoke it.

        Parameters
        ----------
        attrs: List[Union[:class:`discord.Guild`, :class:`discord.Member`, :class:`discord.TextChannel`, :class:`discord.Thread`, :class:`discord.User`]]
            Custom attributes that will be overriden when invoking the command.
        command_name: :class:`str`
            The qualified name of the command to invoke.
        """
        kwargs: dict[str, Any] = {"content": f"{ctx.prefix}{command_name}"}
        for attr in attrs:
            if isinstance(attr, (discord.User, discord.Member)):
                kwargs["author"] = attr
            elif isinstance(attr, discord.Guild):
                kwargs["guild"] = attr
            elif isinstance(attr, (discord.TextChannel, discord.Thread)):
                kwargs["channel"] = attr
        #  Try to upgrade to a Member using the given guild
        guild: Optional[discord.Guild] = kwargs.get("guild")
        author: Optional[discord.User] = kwargs.get("author")
        if guild is not None and author is not None:
            kwargs["author"] = guild.get_member(author.id) or author
        elif guild is None and author is not None and ctx.guild is not None:
            kwargs["author"] = ctx.guild.get_member(author.id) or author

        assert ctx.invoked_with is not None
        invokable = await self._get_invokable(ctx, command_name, kwargs)
        if invokable is None:
            return await send(ctx, f"Command `{command_name}` not found.")
        args = *invokable, "reinvoke" if ctx.invoked_with.endswith("!") else "invoke"
        await self._execute_invokable(*args)

    async def _execute_invokable(
        self,
        command: Union[SyntheticInteraction[types.Bot], types.Command],
        ctx: commands.Context[types.Bot],
        action: Literal["invoke", "reinvoke"] = "invoke",
    ) -> None:
        await getattr(command, action)(ctx)

    async def _get_invokable(
        self, ctx: commands.Context[types.Bot], content: str, kwargs: Dict[str, Any]
    ) -> Optional[Tuple[Union[SyntheticInteraction[types.Bot], types.Command], commands.Context[types.Bot]]]:
        if content.startswith("/"):
            app_commands = self.bot.tree.get_commands(type=discord.AppCommandType.chat_input)
            app_command = get_app_command(content[1:].split("\n")[0], app_commands.copy())  # type: ignore
            if app_command is None:
                return
            kwargs["content"] = kwargs["content"].removeprefix(ctx.prefix)
            context = await generate_ctx(ctx, **kwargs)
            return SyntheticInteraction(context, app_command, await get_parameters(context, app_command)), context
        context = await generate_ctx(ctx, **kwargs)
        if context.command is not None:
            return context.command, context
