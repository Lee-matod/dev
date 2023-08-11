# -*- coding: utf-8 -*-

"""
dev.plugins.management
~~~~~~~~~~~~~~~~~~~~~~

Bot and extension management commands.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import pathlib
import time
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Set, Tuple, Union

import discord
from discord import app_commands
from discord.ext import commands

from dev import root
from dev.components import AuthoredMixin, PermissionsSelector, SettingsToggler
from dev.utils.functs import send
from dev.utils.utils import codeblock_wrapper, escape, format_exception, plural

if TYPE_CHECKING:
    from dev import types

_EXTENSION_EMOJIS = {
    "load": "\N{INBOX TRAY}",
    "reload": "\N{ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS}",
    "unload": "\N{OUTBOX TRAY}",
}


class RootManagement(root.Plugin):
    """Management commands for this extension and the bot"""

    @root.command("settings", parent="dev")
    async def root_settings(self, ctx: commands.Context[types.Bot]):
        """Change or edit this extension's configuration."""
        view = AuthoredMixin(ctx.author)
        SettingsToggler.from_view(view)
        await send(ctx, view)

    @root.command("permissions", parent="dev", aliases=["perms"])
    async def root_permissions(
        self,
        ctx: commands.Context[types.Bot],
        channel: Optional[Union[discord.abc.GuildChannel, discord.Thread]] = None,
    ):
        """Show the permissions the bot has globally or for a channel.

        Parameters
        ----------
        channel: Optional[Union[:class:`discord.abc.GuildChannel`, :class:`discord.Thread`]]
            The specific channel to check permissions for.
        """
        if ctx.guild is None:
            return await send(ctx, "Please execute this command in a guild.")
        select = PermissionsSelector(target=ctx.guild.me, channel=channel)  # type: ignore
        await send(
            ctx,
            discord.Embed(
                description="\n".join(["```ansi", *select.sort_perms("general"), "```"]), color=discord.Color.blurple()
            ),
            AuthoredMixin(ctx.author, select),
        )

    @root.command("load", parent="dev", aliases=["reload", "unload"])
    async def root_load(self, ctx: commands.Context[types.Bot], *extensions: str):
        r"""Load, reload, or unload a set of extensions.
        
        `\~` references all currently loaded extensions; `module.\*` includes all extensions in `module`.

        Parameters
        ----------
        extensions: :class:`str`
            The name of the extensions to take action on.
        """
        invoked_with: Literal["load", "reload", "unload"] = ctx.invoked_with  # type: ignore
        if not extensions:
            extensions = tuple(self.bot.extensions)
        emoji = _EXTENSION_EMOJIS[invoked_with]

        successful: int = 0
        output: List[str] = []
        coro = getattr(self.bot, f"{invoked_with}_extension")
        final = self._resolve_extensions(extensions)
        start = time.perf_counter()
        for ext in final:
            try:
                await coro(ext)
            except commands.ExtensionError as exc:
                output.append(f"\N{WARNING SIGN}\N{VS16} {ext}: {exc}")
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

    @root.command("sync", parent="dev")
    async def root_sync(
        self, ctx: commands.Context[types.Bot], target: Optional[Literal[".", "*", "~.", "~*", "~"]], *guilds: int
    ):
        r"""Sync this bot's application tree with Discord.

        To change sync targets, use `.` to sync to the current guild; `*` to copy all global commands to the
        current guild; omit to sync globally.

        Using the inverter (`~`) causes `~` to clear all global commands or from the given guilds;
        `~.` clears all commands from the current guild; `~*` copies all global commands to the given guilds.

        Parameters
        ----------
        target: Literal[".", "*", "~.", "~*", "~"]
            What should be done with the application tree.
        guilds: :class:`int`
            The guilds to sync the tree to. Not always necessary.
        """
        if not self.bot.application_id:
            return await send(ctx, "Unable to sync. Application information has not been fetched.")

        syncing_guild: Optional[discord.Guild] = ctx.guild
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
            skipped: Set[int] = set()
            global_menus: List[app_commands.ContextMenu] = [
                cmd for menu, cmd in self.bot.tree._context_menus.items() if menu[1] is None
            ]
            for guild_id in guilds:
                mapping: Dict[int, Dict[str, Union[app_commands.Command[Any, ..., Any], app_commands.Group]]] = self.bot.tree._guild_commands.get(guild_id, {}).copy()  # type: ignore
                mapping.update(self.bot.tree._global_commands)  # type: ignore
                local_menus: List[app_commands.ContextMenu] = [
                    cmd
                    for menu, cmd in self.bot.tree._context_menus.items()
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
        guild_set: Set[Optional[discord.abc.Snowflake]] = set(map(discord.Object, guilds))
        if not guilds:
            if target is None:
                syncing_guild = None
            guild_set.add(syncing_guild)
        successful_commands = 0
        successful_guilds: Set[str] = set()
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
            f"\N{SATELLITE} Successfully {fmt} across {plural(len(successful_guilds), 'guild')}.\n"
            + "\n".join(successful_guilds),
            forced=True,
        )

    def _resolve_extensions(self, extensions: Tuple[str, ...], /) -> Set[str]:
        all_extensions: Set[str] = set()
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
            else:
                all_extensions.add(ext)
        return all_extensions
