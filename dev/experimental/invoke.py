# -*- coding: utf-8 -*-

"""
dev.experimental.invoke
~~~~~~~~~~~~~~~~~~~~~~~

Command invocation or reinvocation with changeable execution attributes.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
import io
from typing import (
    List,
    Optional,
    Sequence,
    Union
)

import contextlib
import discord

from discord.ext import commands

from dev.handlers import ExceptionHandler
from dev.types import BotT

from dev.utils.baseclass import Root, root
from dev.utils.functs import generate_ctx, send
from dev.utils.startup import Settings


class ReinvokeFlags(commands.FlagConverter):
    has_: Optional[str] = commands.flag(name="has", default=None)
    startswith_: Optional[str] = commands.flag(name="startswith", default=None)
    endswith_: Optional[str] = commands.flag(name="endswith", default=None)


class NoSendContext(commands.Context):
    async def send(
        self,
        content: Optional[str] = None,
        *,
        tts: bool = False,
        embed: Optional[discord.Embed] = None,
        embeds: Optional[Sequence[discord.Embed]] = None,
        file: Optional[discord.File] = None,
        files: Optional[Sequence[discord.File]] = None,
        stickers: Optional[Sequence[Union[discord.GuildSticker, discord.StickerItem]]] = None,
        delete_after: Optional[float] = None,
        nonce: Optional[Union[str, int]] = None,
        allowed_mentions: Optional[discord.AllowedMentions] = None,
        reference: Optional[Union[discord.Message, discord.MessageReference, discord.PartialMessage]] = None,
        mention_author: Optional[bool] = None,
        view: Optional[discord.ui.View] = None,
        suppress_embeds: bool = False,
        ephemeral: bool = False
    ):
        args: List[str] = [f"{tts = }", f"{suppress_embeds = }", f"{ephemeral = }", f"{mention_author = }"]
        embed_format = "embed = title: {0.title}\n" \
                       "        description: {0.description}\n" \
                       "        color: {0.color}\n" \
                       "        author: {0.author}\n" \
                       "        footer: {0.footer}\n" \
                       "        url: {0.url}\n" \
                       "        timestamp: {0.timestamp}\n" \
                       "        image: {0.image.url}\n" \
                       "        video: {0.video.url}"
        fields_format = "        fields = name: {0.name}\n" \
                        "                 value: {0.value}\n" \
                        "                 inline: {0.inline}"
        if content:
            args.append(f"content = {content}")
        if embed:
            body = embed_format.format(embed)
            fields = []
            if embed.fields:
                for field in embed.fields:
                    fields.append(fields_format.format(field))
            fields = "\n" + "\n".join(fields)
            args.append(f"{body}{fields}")
        if embeds:
            for e in embeds:
                body = embed_format.format(e)
                fields = []
                if e.fields:
                    for field in e.fields:
                        fields.append(fields_format.format(field))
                fields = "\n" + "\n".join(fields)
                args.append(f"{body}{fields}")
        if file:
            args.append(f"file = filename: {file.filename}"
                        f"       content: {file.fp.read()}")
        if files:
            for f in files:
                args.append(f"file = filename: {f.filename}"
                            f"       content: {f.fp.read()}")
        if stickers:
            args.append(f"stickers = {', '.join(f'<name={sticker.name} id={str(sticker.id)}>' for sticker in stickers)}")
        if delete_after:
            args.append(f"{delete_after = }")
        if nonce:
            args.append(f"{nonce = }")
        if allowed_mentions:
            args.append(f"{allowed_mentions = }")
        if reference:
            args.append(f"reference = <id={reference.id} jump_url={reference.jump_url}>")

        print("\n".join(args))


class RootInvoke(Root):
    def __init__(self, bot: BotT):
        super().__init__(bot)

    @root.command(name="no_send", parent="dev", aliases=["ns", "nosend"])
    async def root_no_send(self, ctx: commands.Context, *, command_string: str):
        """Instead of sending a message via `ctx.send`, the message will be redirected to stdout.
        Note that this won't work for all types of `discord.abc.Messageable`, only for `ctx.send`.
        If stdout was already redirected once the message was sent, then the command won't work either (for obvious reasons).
        So make sure to exit your stdout manager before sending any messages if you want to use this command properly.
        """
        kwargs = {"content": f"{ctx.prefix}{command_string}", "author": ctx.author, "channel": ctx.channel}
        context = await generate_ctx(ctx, **kwargs)
        context.__class__ = NoSendContext
        if not context.command:
            return await send(ctx, f"Command `{context.invoked_with}` not found.")
        await context.command.reinvoke(context)

    @root.command(name="no_print", parent="dev", aliases=["np", "noprint"])
    async def root_no_print(self, ctx: commands.Context, *, command_string: str):
        """If there are any print statements in the command, they will be ignored and sent via a Discord message.
        Note that this won't work if the stdout is already being redirected to another file.
        """
        kwargs = {"content": f"{ctx.prefix}{command_string}", "author": ctx.author, "channel": ctx.channel}
        context = await generate_ctx(ctx, **kwargs)
        if not context.command:
            return await send(ctx, f"Command `{context.invoked_with}` not found.")
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            await context.command.reinvoke(context)
        resp = (f"**stdout**\n```py\n{out}\n```" if (out := stdout.getvalue()) else '') + ("\n" if out else '') + (f"**stderr**\n```py\n{err}\n```" if (err := stderr.getvalue()) else '')
        if resp:
            await send(ctx, discord.Embed(title="Output", description=resp, colour=discord.Color.blurple()))

    @root.command(name="repeat", parent="dev", aliases=["repeat!"])
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

    @root.command(name="debug", parent="dev", aliases=["dbg"])
    async def root_debug(self, ctx: commands.Context, *, command_string: str):
        """Catch errors when executing a command.
        This command will probably not catch errors with commands that already have an error handler.
        If `Settings.PATH_TO_FILE` is specified, any instances of this path will be removed if a traceback is sent. Defaults to the current working directory.
        """
        kwargs = {"content": f"{ctx.prefix}{command_string}", "author": ctx.author, "channel": ctx.channel}
        context: commands.Context = await generate_ctx(ctx, **kwargs)
        if not context.command:
            return await send(ctx, f"Command `{context.invoked_with}` not found.")
        async with ExceptionHandler(ctx.message, send_traceback=True) as handler:
            await context.command.invoke(context)
        if handler.error:
            embeds = [discord.Embed(title=exc[0], description=f"```py\n{exc[1].replace(Settings.PATH_TO_FILE, '')}\n```", color=discord.Color.red()) for exc in handler.error]
            handler.cleanup()
            await send(ctx, embeds)
        else:
            await ctx.message.add_reaction("☑")

    @root.command(name="execute", parent="dev", aliases=["exec", "execute!", "exec!"])
    async def root_execute(self, ctx: commands.Context, attrs: commands.Greedy[Union[discord.Member, discord.TextChannel, discord.Thread, discord.Role]], *, command_attr: str):
        """Execute a command with custom attributes.
        Attributes support types are `discord.Member`, `discord.Role`, `discord.TextChannel` and `discord.Thread`. These will override the current context, thus executing the command as another user, text channel and/or with another role.
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
    async def root_reinvoke(self, ctx: commands.Context, skip_message: Optional[int] = 0, author: Optional[discord.Member] = None, *, flags: ReinvokeFlags):
        """Reinvoke the last command that was executed.
        By default, it will try to get the last command that was executed, excluding `dev reinvoke` (for obvious reasons).
        If `invoke` is used instead of reinvoke, command checks will not be ignored.
        If `Message.reference` is not of type `None`, then it will try to reinvoke the command that was executed in the reference. This method of reinvocation ignores all other options and flags.
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
            if message.author == author:
                if "dev reinvoke" in message.content or "dev invoke" in message.content:
                    skip_message += 1
                    c += 1
                    continue
                if c == skip_message:
                    if flag_checks(message, flags):
                        context: commands.Context = await generate_ctx(ctx, ctx.author, ctx.channel, content=message.content)
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
