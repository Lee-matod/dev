# -*- coding: utf-8 -*-

"""
dev.config.bot
~~~~~~~~~~~~~~

Direct bot reconfiguration and attributes manager.

:copyright: Copyright 2023 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from dev.handlers import optional_raise
from dev.components import AuthoredView, PermissionsSelector

from dev.utils.baseclass import Root, root
from dev.utils.functs import send
from dev.utils.utils import escape, parse_invoked_subcommand, plural

if TYPE_CHECKING:
    from dev import types


class RootBot(Root):

    @root.group(name="bot", parent="dev", global_use=True, invoke_without_command=True)
    async def root_bot(self, ctx: commands.Context[types.Bot]):
        """Get a briefing on some bot information."""
        if self.bot.user is None:
            return await send(ctx, "This is not a bot.")
        embed = discord.Embed(
            title=self.bot.user,
            description=self.bot.description or '',
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        mapping = {True: "enabled", False: "disabled", None: "unknown"}
        bot_field = ""
        visibility_field = (
                f"This bot can see {plural(len(self.bot.guilds), 'guild')}, "
                + plural(
            len([c for c in self.bot.get_all_channels() if not isinstance(c, discord.CategoryChannel)]),
            "channel"
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
            f"This bot is running with an average websocket latency of {round(self.bot.latency * 1000, 2)}ms. "
            f"Members intent is {mapping.get(self.bot.intents.members)}, "
            f"message content intent is {mapping.get(self.bot.intents.message_content)} "
            f"and presences intent is {mapping.get(self.bot.intents.presences)}."
        )
        if self.bot.owner_ids:
            bot_field += (
                f"<@!{'>, <@!'.join(f'{owner}' for owner in self.bot.owner_ids)}> are the owners of this bot. "
                f"The prefix of this bot is `{escape(ctx.prefix or 'None')}` "
                f"(case insensitive is {mapping.get(self.bot.case_insensitive)} "
                f"and strip after prefix is {mapping.get(self.bot.strip_after_prefix)}) "
            )
        elif self.bot.owner_id:
            bot_field += (
                f"<@!{self.bot.owner_id}> is the owner of this bot. "
                f"The prefix of this bot is `{escape(ctx.prefix or 'None')}` "
                f"(case insensitive is {mapping.get(self.bot.case_insensitive)} "
                f"and strip after prefix is {mapping.get(self.bot.strip_after_prefix)}) "
            )
        if isinstance(self.bot, commands.AutoShardedBot):
            bot_field += f"and it's automatically sharded: shards {self.bot.shard_id} of {self.bot.shard_count} "
        elif self.bot.shard_count:
            bot_field += f"and it's manually sharded: shards {self.bot.shard_id} of {self.bot.shard_count} "
        else:
            bot_field += "and it's not sharded."
        embed.add_field(name="Bot", value=bot_field, inline=False)
        embed.add_field(name="Visibility", value=visibility_field, inline=False)
        embed.add_field(name="Commands", value=commands_field, inline=False)
        embed.add_field(name="Information", value=information_field, inline=False)
        await send(ctx, embed)

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
                description="\n".join(["```ansi", *select.sort_perms("general"), "```"]),
                color=discord.Color.blurple()
            ),
            AuthoredView(ctx.author, select)
        )

    @root.command(name="load", parent="dev bot", require_var_positional=True)
    async def root_bot_load(self, ctx: commands.Context[types.Bot], *extensions: str):
        """Load a set of extensions"""
        successful: list[str] = []
        unsuccessful: list[str] = []
        start = time.perf_counter()
        for ext in extensions:
            try:
                await self.bot.load_extension(ext)
            except commands.ExtensionError as exc:
                unsuccessful.append(f"{ext} ‒ {exc}")
            else:
                successful.append(ext)
        end = time.perf_counter()
        loaded_extensions = (
                ("\u2611 " + "\n\u2611 ".join(successful) if successful else "")
                + ("\n\u274c " + "\n\u274c ".join(unsuccessful) if unsuccessful else "")
        )
        embed = discord.Embed(
            title=f"Unloaded {plural(len(successful), 'Cog')}",
            description=loaded_extensions.strip("\n"),
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Unloading took {end - start:.3f}s")
        await send(ctx, embed)

    @root.command(name="unload", parent="dev bot", require_var_positional=True)
    async def root_bot_unload(self, ctx: commands.Context[types.Bot], *extensions: str):
        """Unload a set of extensions"""
        successful: list[str] = []
        unsuccessful: list[str] = []
        start = time.perf_counter()
        for ext in extensions:
            try:
                await self.bot.unload_extension(ext)
            except commands.ExtensionError as exc:
                unsuccessful.append(f"{ext} ‒ {exc}")
            else:
                successful.append(ext)
        end = time.perf_counter()
        unloaded_extensions = (
                ("\u2611 " + "\n\u2611 ".join(successful) if successful else "")
                + ("\n\u274c " + "\n\u274c ".join(unsuccessful) if unsuccessful else "")
        )
        embed = discord.Embed(
            title=f"Loaded {plural(len(successful), 'Cog')}",
            description=unloaded_extensions.strip("\n"),
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Loading took {end - start:.3f}s")
        await send(ctx, embed)

    @root.command(name="reload", parent="dev bot")
    async def root_bot_reload(self, ctx: commands.Context[types.Bot], *extensions: str):
        """Reload all or a specific set of bot extension(s).
        When adding specific extensions, each one must be separated but a blank space.
        """
        if not extensions:
            successful: list[str] = []
            unsuccessful: list[str] = []
            start = time.perf_counter()
            for ext in list(self.bot.extensions):
                try:
                    await self.bot.reload_extension(ext)
                except commands.ExtensionError as exc:
                    unsuccessful.append(f"{ext} ‒ {exc}")
                else:
                    successful.append(ext)
            end = time.perf_counter()
            reloaded_extensions = (
                    ("\u2611 " + "\n\u2611 ".join(successful) if successful else "")
                    + ("\n\u274c " + "\n\u274c ".join(unsuccessful) if unsuccessful else "")
            )
            embed = discord.Embed(
                title=f"Reloaded {plural(len(successful), 'Cog')}",
                description=reloaded_extensions.strip("\n"),
                color=discord.Color.blurple()
            )
            embed.set_footer(text=f"Reloading took {end - start:.3f}s.")
            return await send(ctx, embed)

        successful = []
        unsuccessful = []
        start = time.perf_counter()
        for ext in extensions:
            try:
                await self.bot.reload_extension(ext)
            except commands.ExtensionError as e:
                unsuccessful.append(f"{ext} ‒ {e}")
            else:
                successful.append(ext)
        end = time.perf_counter()
        reloaded_extensions = (
                ("\u2611 " + "\n\u2611 ".join(successful) if successful else "") +
                ("\u274c " + "\n\u274c ".join(unsuccessful) if unsuccessful else '')
        )
        embed = discord.Embed(
            title=f"Reloaded {plural(len(successful), 'Cog')}",
            description=reloaded_extensions,
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Reloading took {end - start:.3f}s.")
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
        elif command.name.startswith("dev"):
            return await send(ctx, "Cannot disable dev commands.")
        elif not command.enabled:
            return await send(ctx, f"Command `{command_name}` is already disabled.")
        command.enabled = False
        await ctx.message.add_reaction("\u2611")

    @root.command(name="close", parent="dev bot")
    async def root_bot_close(self, ctx: commands.Context[types.Bot]):
        """Close the bot."""
        await ctx.message.add_reaction("\U0001f44b")
        await self.bot.close()

    @root_bot.error
    async def root_bot_error(self, ctx: commands.Context[types.Bot], exception: commands.CommandError):
        if isinstance(exception, commands.TooManyArguments):
            assert ctx.prefix is not None and ctx.invoked_with is not None
            return await send(
                ctx,
                f"`dev {ctx.invoked_with}` has no subcommand "
                f"`{parse_invoked_subcommand(ctx)}`."
            )
        optional_raise(ctx, exception)
