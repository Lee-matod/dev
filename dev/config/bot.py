# -*- coding: utf-8 -*-

"""
dev.config.bot
~~~~~~~~~~~~~~

Direct bot reconfiguration and attributes manager.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import pathlib
import time
from typing import TYPE_CHECKING, Literal

import discord
from discord.ext import commands

from dev import root
from dev.components import AuthoredView, PermissionsSelector
from dev.utils.functs import send
from dev.utils.utils import escape, plural

if TYPE_CHECKING:
    from dev import types


class RootBot(root.Container):
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

    @root.command(name="load", parent="dev bot", aliases=["reload", "unload"])
    async def root_bot_load(self, ctx: commands.Context[types.Bot], *extensions: str):
        r"""Load, reload, or unload a set of extensions.
        To prevent noisy errors, cogs are checked if they currently exist when loading or unloading.
        - Use '~' to reference all currently loaded cogs.
        - Use 'module.\*' to include all files in 'module'.
        - Use '!cog' to exclude it from being (re/un)loaded.
        """
        invoked_with: Literal["load", "reload", "unload"] = ctx.invoked_with  # type: ignore
        if not extensions:
            extensions = tuple(self.bot.extensions)

        successful, output, perf = await self._manage_extensions(invoked_with, extensions)
        embed = discord.Embed(
            title=f"{invoked_with.title()}ed {plural(successful, 'Cog')}",
            description=escape(output),
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=f"{invoked_with.title()}ing took {perf:.3f}s")
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

    async def _manage_extensions(
        self, action: Literal["load", "reload", "unload"], extensions: tuple[str, ...]
    ) -> tuple[int, str, float]:
        emojis = {"load": "\U0001f4e5", "reload": "\U0001f504", "unload": "\U0001f4e4"}
        emoji = emojis[action]

        loaded_extensions = list(self.bot.extensions)
        successful: int = 0
        output: list[str] = []
        coro = getattr(self.bot, f"{action}_extension")
        final, exclude = self._resolve_extensions(extensions)
        start = time.perf_counter()
        for ext in final:
            if ext in exclude:
                continue
            if action == "load" and ext in loaded_extensions:
                output.append(f"\U0001f4f6 {ext}: Already a loaded extension.")
            elif action == "unload" and ext not in loaded_extensions:
                output.append(f"\U0001f6a9 {ext}: Not a loaded extension.")
            else:
                try:
                    await coro(ext)
                except commands.ExtensionError as exc:
                    output.append(f"\u26a0 {ext}: {exc}")
                else:
                    successful += 1
                    output.append(f"{emoji} {ext}")
        end = time.perf_counter()
        return successful, "\n".join(output), end - start

    def _resolve_extensions(self, extensions: tuple[str, ...], /) -> tuple[set[str], set[str]]:
        all_extensions: set[str] = set()
        excluded_extensions: set[str] = set()
        for ext in extensions:
            if ext == "~":
                all_extensions.update(self.bot.extensions)
            elif ext.endswith(".*"):
                path = pathlib.Path(*ext[:-2].split("."))
                if not path.is_dir():
                    continue
                for subpath in path.glob("*.py"):
                    parts = subpath.with_suffix("").parts
                    if parts[0] == ".":
                        parts = parts[1:]
                    all_extensions.add(".".join(parts))

                for subpath in path.glob("*/__init__.py"):
                    parent, *folders = subpath.parent.parts
                    if parent == ".":
                        all_extensions.add(".".join(folders))
                    else:
                        all_extensions.add(".".join({parent, *folders}))
            elif ext.startswith("!"):
                excluded_extensions.add(ext)
            else:
                all_extensions.add(ext)
        return all_extensions, excluded_extensions
