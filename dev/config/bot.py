# -*- coding: utf-8 -*-

"""
dev.config.bot
~~~~~~~~~~~~~~

Direct bot reconfiguration and attributes manager.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""


import time
from typing import Literal, Optional

import discord
from discord.ext import commands

from dev.converters import LiteralModes, convert_str_to_ints
from dev.handlers import optional_raise

from dev.utils.baseclass import Root, root
from dev.utils.functs import all_commands, send
from dev.utils.utils import escape, plural


class RootBot(Root):

    @root.group(name="bot", parent="dev", invoke_without_command=True, global_use=True)
    async def root_bot(self, ctx: commands.Context):
        """Get a briefing of the bot's characteristics"""
        embed = discord.Embed(title=self.bot.user, description=self.bot.description or '', color=discord.Color.blurple())
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        mapping = {True: "enabled", False: "disabled", None: "unknown"}
        bot_field = f""
        visibility_field = (f"This bot can see {plural(len(self.bot.guilds), 'guild')}, "
                            f"{plural(len([c for c in self.bot.get_all_channels() if not isinstance(c, discord.CategoryChannel)]), 'channel')} "
                            f"and {plural(len(self.bot.users), 'account')}, "
                            f"{len([user for user in self.bot.users if not user.bot])} of which are users.")
        commands_field = (f"There is a total of {len(all_commands(self.bot.commands))} commands "
                          f"and {len(self.bot.extensions)} loaded {plural(len(self.bot.extensions), 'extension', False)}.")
        information_field = (f"This bot is running with an average websocket latency of {round(self.bot.latency * 1000, 2)}ms. "
                             f"Members intent is {mapping.get(self.bot.intents.members)}, "
                             f"message content intent is {mapping.get(self.bot.intents.message_content)} "
                             f"and presences intent is {mapping.get(self.bot.intents.presences)}.")
        if self.bot.owner_ids:
            bot_field += (f"<@!{'>, <@!'.join(f'{owner}' for owner in self.bot.owner_ids)}> are the owners of this bot. "
                          f"The prefix of this bot is `{escape(ctx.prefix)}` "
                          f"(case insensitive is {mapping.get(self.bot.case_insensitive)} "
                          f"and strip after prefix is {mapping.get(self.bot.strip_after_prefix)}) ")
        elif self.bot.owner_id:
            bot_field += (f"<@!{self.bot.owner_id}> is the owner of this bot. "
                          f"The prefix of this bot is `{escape(ctx.prefix)}` "
                          f"(case insensitive is {mapping.get(self.bot.case_insensitive)} "
                          f"and strip after prefix is {mapping.get(self.bot.strip_after_prefix)}) ")
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

    @root_bot.command(name="reload")
    async def root_bot_reload(self, ctx: commands.Context, *cogs: str):
        """Reload all or a specific set of the bot's extension(s)
        If specific cogs are specified, they should be separated by a blank space.
        """
        if not cogs:
            successful = []
            unsuccessful = []
            start = time.perf_counter()
            for ext in list(self.bot.extensions):
                try:
                    await self.bot.reload_extension(ext)
                    successful.append(ext)
                except commands.ExtensionError as e:
                    unsuccessful.append(f"{ext} ??? {e}")
            end = time.perf_counter()
            reloaded_cogs = ("??? " + "\n??? ".join(successful) if successful else "") + ("??? " + "\n??? ".join(unsuccessful) if unsuccessful else '')
            embed = discord.Embed(title=f"Reloaded {plural(len(successful), 'Cog')}", description=reloaded_cogs, color=discord.Color.blurple())
            embed.set_footer(text=f"Reloading took {end - start:.3f}s.")
            return await send(ctx, embed)

        successful = []
        unsuccessful = []
        start = time.perf_counter()
        for cog in cogs:
            try:
                await self.bot.reload_extension(cog)
                successful.append(cog)
            except commands.ExtensionError as e:
                unsuccessful.append(f"{cog} ??? {e}")
        end = time.perf_counter()
        reloaded_cogs = ("??? " + "\n??? ".join(successful) if successful else "") + ("??? " + "\n??? ".join(unsuccessful) if unsuccessful else '')
        embed = discord.Embed(title=f"Reloaded {plural(len(successful), 'Cog')}", description=reloaded_cogs, color=discord.Color.blurple())
        embed.set_footer(text=f"Reloading took {end - start:.3f}s.")
        return await send(ctx, embed)

    @root_bot.command(name="edit")
    async def root_bot_edit(self, ctx: commands.Context, attr: LiteralModes[Literal["prefix", "owner", "owners"]], *, value: Optional[str] = None):
        """Edit any attributed of the bot.
        **Text Placeholders**
        `__existent__` = Keep already existent values of the specified attribute and add new ones (if specified).
        **Attributes**
        `prefix` = Change the prefix of the bot.
        `owner`|`owners` = Change, add or view current owner ID(s).
        """
        if attr is None:
            return
        if attr == "prefix":
            if not value:
                return await send(ctx, f"{attr}: `{escape(self.bot.command_prefix)}`")
            self.bot.command_prefix = value
            await send(ctx, f"Successfully changed `{attr}` to `{escape(value)}`")

        elif attr == "owner":
            if self.bot.owner_ids:
                return await send(ctx, f"Cannot set `owner_id` if `owner_ids` is not None.")
            if not value:
                return await send(ctx, f"{attr}: `{self.bot.owner_id or 'None'}`")
            elif not value.isnumeric():
                return await send(ctx, f"`{attr}` has to be of type _int_.")
            elif value.lower() == "none":
                self.bot.owner_id = None
                return await send(ctx, f"Successfully set `{attr}` to None.")
            self.bot.owner_id = int(value)
            await send(ctx, f"Successfully changed `{attr}` to `{self.bot.owner_id}`")

        elif attr == "owners":
            if self.bot.owner_id:
                return await send(ctx, f"Cannot set `owner_ids` if `owner_id` is not None.")
            if not value:
                return await send(ctx, f"{attr}: `{'`, `'.join(owner for owner in self.bot.owner_ids) or '{}'}`")
            if "__existent__" in value:
                value = value.replace("__existent__", ", ".join(owner for owner in self.bot.owner_ids), 1)
            elif value.lower() == "none":
                self.bot.owner_ids = None
                return await send(ctx, f"Successfully set `{attr}` to None.")
            ids = convert_str_to_ints(value)
            self.bot.owner_ids = set(ids)
            await send(ctx, f"Successfully changed `{attr}` to `{'`, `'.join(str(owner) for owner in self.bot.owner_ids) or 'None'}`")

    @root_bot.command(name="enable", require_var_positional=True)
    async def root_bot_enable(self, ctx: commands.Context, *, command_name: str):
        """Enable a command.
        It is not recommended to disable this command using `dev bot disable`.
        """
        command = self.bot.get_command(command_name)
        if not command:
            return await send(ctx, f"Command `{command_name}` not found.")
        if command.enabled:
            return await send(ctx, f"Command `{command_name}` is already enabled.")
        command.enabled = True
        await ctx.message.add_reaction("???")

    @root_bot.command(name="disable", require_var_positional=True)
    async def root_bot_disable(self, ctx: commands.Context, *, command_name: str):
        """Disable a command.
        It is not recommended to disable the `dev bot enable` command.
        """
        command = self.bot.get_command(command_name)
        if not command:
            return await send(ctx, f"Command `{command_name}` not found.")
        elif command.name.startswith("dev"):
            return await send(ctx, "Cannot disable dev commands.")
        elif not command.enabled:
            return await send(ctx, f"Command `{command_name}` is already disabled.")
        command.enabled = False
        await ctx.message.add_reaction("???")

    @root_bot.command(name="close")
    async def root_bot_close(self, ctx: commands.Context):
        """Closes the bot."""
        await ctx.message.add_reaction("????")
        await self.bot.close()

    @root_bot.error
    async def root_bot_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.TooManyArguments):
            return await send(ctx, f"`dev bot` has no subcommand called `{ctx.subcommand_passed}`.")
        optional_raise(ctx, error)
