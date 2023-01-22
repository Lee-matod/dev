# -*- coding: utf-8 -*-

"""
dev.config.bot
~~~~~~~~~~~~~~

Direct bot reconfiguration and attributes manager.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING, Literal

import discord
from discord.ext import commands

from dev.components import AuthoredView, PermissionsSelector
from dev.utils.baseclass import Root, root
from dev.utils.functs import send
from dev.utils.utils import escape, plural

if TYPE_CHECKING:
    from dev import types


class RootBot(Root):
    """Information, statistics, and commands related to this bot's configuration"""

    @root.group(name="bot", parent="dev", global_use=True, invoke_without_command=True)
    async def root_bot(self, ctx: commands.Context[types.Bot]):
        """Get a briefing on some bot information."""
        if self.bot.user is None:
            return await send(ctx, "This is not a bot.")
        embed = discord.Embed(
            title=self.bot.user,
            description=self.bot.description or "",
            color=discord.Color.blurple(),
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        mapping = {True: "enabled", False: "disabled", None: "unknown"}
        bot_field = ""
        visibility_field = (
            f"This bot can see {plural(len(self.bot.guilds), 'guild')}, "
            + plural(
                len([c for c in self.bot.get_all_channels() if not isinstance(c, discord.CategoryChannel)]),
                "channel",
            )
            + f" and {plural(len(self.bot.users), 'account')}, "
            f"{len([user for user in self.bot.users if not user.bot])} of which are users."
        )
        commands_field = (
            f"There is a total of {len(list(self.bot.walk_commands()))} commands "
            f"and {len(self.bot.extensions)} loaded "
            f"{plural(len(self.bot.extensions), 'extension', False)}."
        )
        information_field = (
            f"Running with a websocket latency of {round(self.bot.latency * 1000, 2)}ms. "
            f"Members intent is {mapping.get(self.bot.intents.members)}, "
            f"message content intent is {mapping.get(self.bot.intents.message_content)} "
            f"and presences intent is {mapping.get(self.bot.intents.presences)}."
        )
        if self.bot.owner_ids:
            bot_field += (
                f"{', '.join(f'<@!{owner}>' for owner in self.bot.owner_ids)} own this bot. "
                f"The prefix is `{escape(ctx.prefix or '')}` "
                f"(case insensitive is {mapping.get(self.bot.case_insensitive)} "
                f"and strip after prefix is {mapping.get(self.bot.strip_after_prefix)}) "
            )
        elif self.bot.owner_id:
            bot_field += (
                f"<@!{self.bot.owner_id}> is the owner of this bot. "
                f"The prefix of this bot is `{escape(ctx.prefix or '')}` "
                f"(case insensitive is {mapping.get(self.bot.case_insensitive)} "
                f"and strip after prefix is {mapping.get(self.bot.strip_after_prefix)}) "
            )
        if isinstance(self.bot, commands.AutoShardedBot):
            bot_field += "and it's automatically sharded:"
            if len(self.bot.shards) > 20:
                bot_field += f"shards {len(self.bot.shards)} of {self.bot.shard_count}"
            elif self.bot.shard_count:
                bot_field += f"shards {self.bot.shard_ids} of {self.bot.shard_count} "
        else:
            bot_field += "and it's not sharded."
        embed.add_field(name="Bot", value=bot_field.strip(), inline=False)
        embed.add_field(name="Visibility", value=visibility_field.strip(), inline=False)
        embed.add_field(name="Commands", value=commands_field.strip(), inline=False)
        embed.add_field(name="Information", value=information_field.strip(), inline=False)
        await send(ctx, embed)

    @root.command(name="permissions", parent="dev bot", aliases=["perms"])
    async def root_bot_permissions(
        self,
        ctx: commands.Context[types.Bot],
        channel: discord.TextChannel | None = None,
    ):
        """Show which permissions the bot has.
        A text channel may be optionally passed to check for permissions in the given channel.
        """
        if ctx.guild is None:
            return await send(ctx, "Please execute this command in a guild.")
        select = PermissionsSelector(target=ctx.guild.me, channel=channel)
        await send(
            ctx,
            discord.Embed(
                description="\n".join(["```ansi", *select.sort_perms("general"), "```"]),
                color=discord.Color.blurple(),
            ),
            AuthoredView(ctx.author, select),
        )

    @root.command(name="load", parent="dev bot", aliases=["reload", "unload"], require_var_positional=True)
    async def root_bot_load(self, ctx: commands.Context[types.Bot], *extensions: str):
        """Load, reload, or unload a set of extensions.
        Use '~' to reference all currently loaded cogs.
        This extension is skipped when loading or unloading.
        """
        assert ctx.invoked_with is not None

        successful, output, perf = await self._manage_extension(ctx.invoked_with, extensions)  # type: ignore
        embed = discord.Embed(
            title=f"{ctx.invoked_with.title()} {plural(successful, 'Cog')}",
            description=output,
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=f"{ctx.invoked_with.title()}ing took {perf:.3f}s")
        await send(ctx, embed)

    @root.command(name="enable", parent="dev bot", require_var_positional=True)
    async def root_bot_enable(self, ctx: commands.Context[types.Bot], *, command_name: str):
        """Enable a command.
        For obvious reasons, it is not recommended to disable this command using `dev bot disable`.
        """
        command = self.bot.get_command(command_name)
        if not command:
            return await send(ctx, f"Command `{command_name}` not found.")
        if command.enabled:
            return await send(ctx, f"Command `{command_name}` is already enabled.")
        command.enabled = True
        await ctx.message.add_reaction("\u2611")

    @root.command(name="disable", parent="dev bot", require_var_positional=True)
    async def root_bot_disable(self, ctx: commands.Context[types.Bot], *, command_name: str):
        """Disable a command.
        For obvious reasons, it is not recommended to disable the `dev bot enable` command.
        """
        command = self.bot.get_command(command_name)
        if not command:
            return await send(ctx, f"Command `{command_name}` not found.")
        if not command.enabled:
            return await send(ctx, f"Command `{command_name}` is already disabled.")
        command.enabled = False
        await ctx.message.add_reaction("\u2611")

    @root.command(name="close", parent="dev bot")
    async def root_bot_close(self, ctx: commands.Context[types.Bot]):
        """Close the bot."""
        await ctx.message.add_reaction("\U0001f44b")
        await self.bot.close()

    async def _manage_extension(
        self, action: Literal["load", "reload", "unload"], extensions: tuple[str, ...]
    ) -> tuple[int, str, float]:
        if action == "load":
            emoji: str = "\U0001f4e5"
        elif action == "unload":
            emoji: str = "\U0001f4e4"
        else:
            emoji: str = "\U0001f504"

        if "~" in extensions:
            extensions = tuple(self.bot.extensions)
        successful: int = 0
        output: list[str] = []
        start = time.perf_counter()
        method = getattr(self.bot, f"{action}_extension")
        for ext in extensions:
            if ext == "dev" and action in ["load", "unload"]:
                continue
            try:
                await method(ext)
            except commands.ExtensionError as exc:
                output.append(f"\u26a0 {ext}: {exc}")
            else:
                successful += 1
                output.append(f"{emoji} {ext}")
        end = time.perf_counter()
        return successful, "\n".join(output), end - start
