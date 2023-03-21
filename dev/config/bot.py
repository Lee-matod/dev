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
from typing import TYPE_CHECKING, Any, Literal

import discord
from discord import app_commands
from discord.ext import commands

from dev import root
from dev.components import AuthoredView, PermissionsSelector
from dev.utils.functs import send
from dev.utils.utils import codeblock_wrapper, escape, format_exception, plural

if TYPE_CHECKING:
    from dev import types

_EXTENSION_EMOJIS = {"load": "\U0001f4e5", "reload": "\U0001f504", "unload": "\U0001f4e4"}


class RootBot(root.Container):
    """Information, statistics, and commands related to this bot's configuration"""

    @root.group(name="bot", parent="dev", global_use=True, invoke_without_command=True)
    async def root_bot(self, ctx: commands.Context[types.Bot]):
        """Get a briefing on some bot information."""
        if self.bot.user is None:
            return await send(ctx, "This is not a bot.")
        embed = discord.Embed(
            title=self.bot.user, description=self.bot.description or "", color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        mapping = {True: "enabled", False: "disabled", None: "unknown"}
        bot_field = ""
        visibility_field = (
            f"This bot can see {plural(len(self.bot.guilds), 'guild')}, "
            + plural(
                len([c for c in self.bot.get_all_channels() if not isinstance(c, discord.CategoryChannel)]), "channel"
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

    @root.command(name="sync", parent="dev bot")
    async def root_bot_sync(
        self, ctx: commands.Context[types.Bot], target: Literal[".", "*", "~.", "~*", "~"] | None, *guilds: int
    ):
        """Sync this bot's application command tree with Discord.
        Omit modes to sync globally.
        **Modes**
        `.`: Sync the current guild.
        `*`: Copy all global commands to the current guild and sync.
        `~`: Inverts the current mode.

        Using the inverter causes the following change in behavoir:
        `~` clears all global commands or local commands from the given guilds.
        `~.` clears all commands from the current guild.
        `~*` copies all global commands to the given guilds.
        """
        if not self.bot.application_id:
            return await send(ctx, "Unable to sync. Application information has not been fetched.")

        syncing_guild: discord.Guild | None = ctx.guild
        if target in {".", "*", "~."}:
            if ctx.guild is None:
                return await send(ctx, "This mode is only available when used in a guild.")
        if target == "*":
            assert ctx.guild is not None
            try:
                self.bot.tree.copy_global_to(guild=ctx.guild)
            except app_commands.CommandLimitReached:
                return await send(
                    ctx, f"Cannot copy global commands because this guild's command limit has been reached."
                )
        elif target == "~.":
            assert ctx.guild is not None
            self.bot.tree.clear_commands(guild=ctx.guild)
        elif target == "~*":
            if not guilds:
                return await send(ctx, "Cannot copy globals to guilds because no guilds were given.")
            skipped: set[int] = set()
            global_menus: list[app_commands.ContextMenu] = [
                cmd
                for menu, cmd in self.bot.tree._context_menus.items()  # pyright: ignore [reportPrivateUsage]
                if menu[1] is None
            ]
            for guild_id in guilds:
                mapping: dict[int, dict[str, app_commands.Command[Any, ..., Any] | app_commands.Group]] = self.bot.tree._guild_commands.get(guild_id, {}).copy()  # type: ignore
                mapping.update(self.bot.tree._global_commands)  # type: ignore
                local_menus: list[app_commands.ContextMenu] = [
                    cmd
                    for menu, cmd in self.bot.tree._context_menus.items()  # pyright: ignore [reportPrivateUsage]
                    if menu[1] is not None and menu[1] == guild_id
                ]
                if len(mapping) > 100 or len({*global_menus, *local_menus}) > 5:
                    skipped.add(guild_id)
            for guild_id in guilds:
                if guild_id in skipped:
                    continue
                #  No exception should be raised here, because we
                #  checked if we could copy them before.
                self.bot.tree.copy_global_to(guild=discord.Object(guild_id))
            if skipped:
                await send(
                    ctx,
                    f"Skipped a total of {plural(len(skipped), 'guild')} because the command limit was reached in those guilds. "
                    f"Skipped guilds were:\n{', '.join(map(str, skipped))}",
                    forced=True,
                )
        elif target == "~":
            if not guilds:
                self.bot.tree.clear_commands(guild=None)
                syncing_guild = None
            else:
                for guild_id in guilds:
                    self.bot.tree.clear_commands(guild=discord.Object(guild_id))
        guild_set: set[discord.abc.Snowflake | None] = set(map(discord.Object, guilds))
        if not guilds:
            if target is None:
                syncing_guild = None
            guild_set.add(syncing_guild)
        successful_commands = 0
        successful_guilds: set[str] = set()
        for guild in guild_set:
            try:
                synced = await self.bot.tree.sync(guild=guild)
            except discord.HTTPException as exc:
                tb = codeblock_wrapper(format_exception(exc), "py")
                guild_str = f"to `{guild.id}`" if guild else "globally"
                await send(ctx, f"An error occurred while syncing {guild_str}:\n{tb}", forced=True)
            else:
                successful_guilds.add(f"`{getattr(guild, 'id', 'Globally')}`")
                successful_commands += len(synced)
        fmt = f"synced {plural(successful_commands, 'application command')}"
        if target is not None and "*" in target:
            fmt = f"copied {plural(successful_commands, 'application command')}"
        elif target is not None and "~" in target:
            fmt = "cleared all commands"
        await send(
            ctx,
            f"\U0001f6f0 Successfully {fmt} across {plural(len(successful_guilds), 'guild')}.\n"
            + "\n".join(successful_guilds),
            forced=True,
        )

    @root.command(name="permissions", parent="dev bot", aliases=["perms"])
    async def root_bot_permissions(self, ctx: commands.Context[types.Bot], channel: discord.TextChannel | None = None):
        """Show which permissions the bot has.
        A text channel may be optionally passed to check for permissions in the given channel.
        """
        if ctx.guild is None:
            return await send(ctx, "Please execute this command in a guild.")
        select = PermissionsSelector(target=ctx.guild.me, channel=channel)
        await send(
            ctx,
            discord.Embed(
                description="\n".join(["```ansi", *select.sort_perms("general"), "```"]), color=discord.Color.blurple()
            ),
            AuthoredView(ctx.author, select),
        )

    @root.command(name="load", parent="dev bot", aliases=["reload", "unload"])
    async def root_bot_load(self, ctx: commands.Context[types.Bot], *extensions: str):
        r"""Load, reload, or unload a set of extensions.
        To prevent noisy errors, extensions are checked if they currently exist when loading or unloading.
        - Use '~' to reference all currently loaded extensions.
        - Use 'module.\*' to include all extensions in 'module'.
        """
        invoked_with: Literal["load", "reload", "unload"] = ctx.invoked_with  # type: ignore
        if not extensions:
            extensions = tuple(self.bot.extensions)
        emoji = _EXTENSION_EMOJIS[invoked_with]

        successful: int = 0
        output: list[str] = []
        coro = getattr(self.bot, f"{invoked_with}_extension")
        final = self._resolve_extensions(extensions)
        start = time.perf_counter()
        for ext in final:
            try:
                await coro(ext)
            except commands.ExtensionError as exc:
                output.append(f"\u26a0 {ext}: {exc}")
            else:
                successful += 1
                output.append(f"{emoji} {ext}")
        end = time.perf_counter()

        embed = discord.Embed(
            title=f"{invoked_with.title()}ed {plural(successful, 'Cog')}",
            description=escape("\n".join(output)),
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=f"{invoked_with.title()}ing took {end-start:.3f}s")
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

    def _resolve_extensions(self, extensions: tuple[str, ...], /) -> set[str]:
        all_extensions: set[str] = set()
        for ext in extensions:
            if ext == "~":
                all_extensions.update(self.bot.extensions)
            elif ext.endswith(".*"):
                all_extensions.update(self._find_extensions_in(ext[:-2].split(".")))
            else:
                all_extensions.add(ext)
        return all_extensions

    def _find_extensions_in(self, ext_parts: list[str], /) -> set[str]:
        path = pathlib.Path(*ext_parts)
        extensions: set[str] = set()
        if not path.is_dir():
            return set()
        for subpath in path.glob("*.py"):
            parts = subpath.with_suffix("").parts
            if parts[0] == ".":
                parts = parts[1:]
            extensions.add(".".join(parts))
        for subpath in path.glob("*/__init__.py"):
            parent, *folders = subpath.parent.parts
            if parent == ".":
                extensions.add(".".join(folders))
            else:
                extensions.add(".".join({parent, *folders}))
        return extensions
