# -*- coding: utf-8 -*-

"""
dev.experimental.invoke
~~~~~~~~~~~~~~~~~~~~~~~

Command invocation or reinvocation with changeable execution attributes.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from typing import Optional, Union

import discord
from discord.ext import commands

from dev.handlers import ExceptionHandler

from dev.utils.baseclass import Root, root
from dev.utils.functs import generate_ctx, send
from dev.utils.interaction import SyntheticInteraction, get_app_command
from dev.utils.startup import Settings


class ReinvokeFlags(commands.FlagConverter):
    has_: Optional[str] = commands.flag(name="has", default=None)
    startswith_: Optional[str] = commands.flag(name="startswith", default=None)
    endswith_: Optional[str] = commands.flag(name="endswith", default=None)


class RootInvoke(Root):

    @root.command(name="repeat", parent="dev", aliases=["repeat!"], require_var_positional=True)
    async def root_repeat(self, ctx: commands.Context, amount: int, *, command_string: str):
        """Call a command `amount` times.
        Checks can be optionally bypassed by using `repeat!` instead of `repeat`.
        """
        kwargs = {"content": f"{ctx.prefix}{command_string}", "author": ctx.author, "channel": ctx.channel}
        for _ in range(amount):
            context = await generate_ctx(ctx, **kwargs)
            if not context.command:
                return await send(ctx, f"Command `{context.invoked_with}` not found.")
            if ctx.invoked_with.endswith("!"):
                await context.command.reinvoke(context)
            else:
                await context.command.invoke(context)

    @root.command(name="debug", parent="dev", aliases=["dbg"], require_var_positional=True)
    async def root_debug(self, ctx: commands.Context, *, command_string: str):
        """Catch errors when executing a command.
        This command will probably not catch errors with commands that already have an error handler.
        If `Settings.PATH_TO_FILE` is specified, any instances of this path will be removed if a traceback is sent.
        """
        kwargs = {"content": f"{ctx.prefix}{command_string}", "author": ctx.author, "channel": ctx.channel}
        context: commands.Context = await generate_ctx(ctx, **kwargs)
        if not context.command:
            return await send(ctx, f"Command `{context.invoked_with}` not found.")
        async with ExceptionHandler(ctx.message, save_traceback=True) as handler:
            await context.command.invoke(context)
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
            ctx: commands.Context,
            attrs: commands.Greedy[
                Union[discord.Member, discord.TextChannel, discord.Thread, discord.Role]
            ],
            *,
            command_attr: str
    ):
        """Execute a command with custom attributes.
        Attribute support types are `discord.Member`, `discord.Role`, `discord.TextChannel` and `discord.Thread`.
        These will override the current context, thus executing the command in a different virtual environment.
        Command checks can be optionally disabled by adding an exclamation mark at the end of the `execute` command.
        """
        kwargs = {"content": f"{ctx.prefix}{command_attr}", "author": ctx.author, "channel": ctx.channel}
        roles = []
        for attr in attrs:
            if isinstance(attr, discord.Member):
                kwargs["author"] = attr
            elif isinstance(attr, (discord.TextChannel, discord.Thread)):
                kwargs["channel"] = attr
            elif isinstance(attr, discord.Role):
                # noinspection PyProtectedMember
                kwargs["author"]._roles.add(attr.id)
                roles.append(attr.id)
        if command_attr.startswith("/"):
            app_commands = self.bot.tree.get_commands(type=discord.AppCommandType.chat_input)
            app_command = get_app_command(command_attr.removeprefix("/"), app_commands.copy())  # type: ignore
            if app_command is None:
                return await send(ctx, "Couldn't find an app (slash) command with that name.")
            kwargs["content"] = kwargs["content"].removeprefix(ctx.prefix)
            context: commands.Context = await generate_ctx(ctx, **kwargs)
            interaction = SyntheticInteraction(context, app_command)
            if ctx.invoked_with.endswith("!"):
                return await interaction.reinvoke()
            return await interaction.invoke()
        context: commands.Context = await generate_ctx(ctx, **kwargs)
        if not context.command:
            for role in roles:
                # noinspection PyProtectedMember
                del kwargs["author"]._roles[role]
            return await ctx.send(f"Command `{context.invoked_with}` not found.")
        try:
            if ctx.invoked_with.endswith("!"):
                return await context.command.reinvoke(context)
            await context.command.invoke(context)
        finally:
            for index, _ in enumerate(roles):
                # noinspection PyProtectedMember
                del kwargs["author"]._roles[-index]

    @root.command(name="reinvoke", parent="dev", aliases=["invoke"])
    async def root_reinvoke(
            self,
            ctx: commands.Context,
            skip_message: Optional[int] = 0,
            author: Optional[discord.Member] = None,
            *,
            flags: ReinvokeFlags):
        """Reinvoke the last command that was executed.
        By default, it will try to get the last command that was executed.
        If `invoke` is used instead of reinvoke, command checks will not be ignored.
        If the command references a message, then it will try to reinvoke the command found in the reference.
        This method of reinvocation ignores all other options and flags.
        **Flag arguments:**
        `has`: _str_ = Check if the message has a specific sequence of characters. Defaults to _None_.
        `startswith`: _str_ = Check if the message startswith a specific characters. Defaults to _None_.
        `endswith`: _str_ = Check if the message endswith a specific characters. Defaults to _None_.
        """
        if ctx.message.reference:
            if ctx.message.reference.resolved.content.startswith(ctx.prefix):
                context: commands.Context = await self.bot.get_context(ctx.message.reference.resolved)
                if ctx.invoked_with == "invoke":
                    return await context.command.invoke(context)
                return await context.command.reinvoke(context)
            return await send(ctx, "No command found in the message reference.")
        author = author or ctx.author
        c = 0
        async for message in ctx.channel.history(limit=100):
            if message.author == author and message.content.startswith(ctx.clean_prefix):
                if "dev reinvoke" in message.content or "dev invoke" in message.content:
                    skip_message += 1
                    c += 1
                    continue
                if c == skip_message:
                    if flag_checks(message, flags):
                        context: commands.Context = await generate_ctx(
                            ctx,
                            ctx.author,
                            ctx.channel,
                            content=message.content
                        )
                        if ctx.invoked_with == "invoke":
                            return await context.command.invoke(context)
                        return await context.command.reinvoke(context)
                c += 1
        await send(ctx, "Unable to find any messages matching the given arguments.")


def flag_checks(message: discord.Message, flags: ReinvokeFlags) -> bool:
    if flags.has_:
        if flags.has_ not in message.content:
            return False
    if flags.startswith_:
        if not message.content.startswith(flags.startswith_):
            return False
    if flags.endswith_:
        if not message.content.endswith(flags.endswith_):
            return False
    return True
