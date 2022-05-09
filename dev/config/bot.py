# -*- coding: utf-8 -*-

"""
dev.config.bot
~~~~~~~~~~~~~~

Direct bot reconfiguration and attributes manager.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""

import time
import discord

from discord.ext import commands

from dev.converters import convert_str_to_ids

from dev.utils.functs import send
from dev.utils.baseclass import root, Root
from dev.utils.utils import escape, plural


class RootBot(Root):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)

    @root.group(name="bot", parent="dev", version=1, invoke_without_command=True)
    async def root_bot(self, ctx: commands.Context):
        """Check bot statistics."""
        is_autosharded = ", automatically sharded" if isinstance(self.bot, commands.AutoShardedBot) else (", manually sharded" if self.bot.shard_count else '')
        shards = f"{self.bot.shard_count or ''} {plural(self.bot.shard_count, 'shard') if self.bot.shard_count else 'no shards'} ({self.bot.shard_id or '0'} of {self.bot.shard_count or '0'}{is_autosharded})"
        owners = (f"<@!{'>, <@!'.join(f'{owner}' for owner in self.bot.owner_ids)}> being my owners" if self.bot.owner_ids else f"<@!{self.bot.owner_id}> being my owner") or 'no owners'
        prefix = f"`{escape(ctx.clean_prefix)}` being my prefix (case insensitive=`{self.bot.case_insensitive}`, strip after prefix=`{self.bot.strip_after_prefix}`)"

        guilds = plural(len(self.bot.guilds), "guild")
        channels = plural(len([channel for channel in self.bot.get_all_channels()]), "channel")
        users = plural(len(self.bot.users), "user")
        real_user, bot_user = plural(len([user for user in self.bot.users if not user.bot]), "real user"), plural(len([user for user in self.bot.users if user.bot and user.bot != self.bot.user]), "bot")

        cmds = plural(len(self.bot.commands), "command")
        cogs = plural(len(self.bot.extensions), "extension")

        latency = round(self.bot.latency * 1000, 2)
        *intents, intent = (f"`{intent.replace('_', ' ')}` intent is set to `{getattr(self.bot.intents, intent, None)}`" for intent in ["members", "message_content", "presences"])

        embed = discord.Embed(title=self.bot.user, description=self.bot.description or 'No description.', color=discord.Color.blurple())
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text=f"{self.bot.user.id}")
        embed.add_field(name="Bot", value=f"Running with {shards}. {owners}, and {prefix}.", inline=False)
        embed.add_field(name="Visibility", value=f"Seeing a total of {guilds}, {channels}, and {users}: {real_user} and {bot_user}.", inline=False)
        embed.add_field(name="Commands", value=f"A total of {cmds} and {cogs} are up for use.", inline=False)
        embed.add_field(name="Information", value=f"Running with an average latency of {latency} ms. {', '.join(intents)} and {intent}.", inline=False)
        await send(ctx, embed=embed)

    @root_bot.command(name="reload", version=1)
    async def root_bot_reload(self, ctx: commands.Context, *cogs: str):
        """Reload all or a specific set of the bot's extension(s)
        If specific cogs are specified, they should be separated by a blank space.
        """
        if not cogs:
            successful = []
            unsuccessful = []
            start = time.perf_counter()
            for ext in list(self.bot.extensions).copy():
                try:
                    await self.bot.reload_extension(ext)
                    successful.append(ext)
                except commands.ExtensionError as e:
                    unsuccessful.append(f"{ext} ‒ {e}")
            end = time.perf_counter()
            reloaded_cogs = ("☑ " + "\n☑ ".join(successful) if successful else "") + ("❌ " + "\n❌ ".join(unsuccessful) if unsuccessful else '')
            embed = discord.Embed(title=f"Reloaded {plural(len(successful), 'Cog')}", description=reloaded_cogs, color=discord.Color.blurple())
            embed.set_footer(text=f"Reloading took {end - start:.3f}s.")
            return await send(ctx, embed=embed)

        successful = []
        unsuccessful = []
        start = time.perf_counter()
        for cog in cogs:
            try:
                await self.bot.reload_extension(cog)
                successful.append(cog)
            except commands.ExtensionError as e:
                unsuccessful.append(f"{cog} ‒ {e}")
        end = time.perf_counter()
        reloaded_cogs = ("☑ " + "\n☑ ".join(successful) if successful else "") + ("❌ " + "\n❌ ".join(unsuccessful) if unsuccessful else '')
        embed = discord.Embed(title=f"Reloaded {plural(len(successful), 'Cog')}", description=reloaded_cogs, color=discord.Color.blurple())
        embed.set_footer(text=f"Reloading took {end - start:.3f}s.")
        return await send(ctx, embed=embed)

    @root_bot.command(name="edit", version=1)
    async def root_bot_edit(self, ctx: commands.Context, attr: str, *, value: str = None):
        """Edit any attributed of the bot.
        **Text Placeholders**
        `__existent__` = Keep already existent values of the specified attribute and add new ones (if specified).
        **Attributes**
        `prefix` = Change the prefix of the bot.
        `owner`|`owners` = Change or add owner ID(s).
        """
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
            ids = convert_str_to_ids(value)
            exec(compile(f"bot.owner_ids = ({', '.join(ids)})", "<repl>", "single"), {"bot": self.bot})  # cause why not lol
            await send(ctx, f"Successfully changed `{attr}` to `{'`, `'.join(str(owner) for owner in self.bot.owner_ids) or 'None'}`")

    @root_bot.command(name="enable", version=1)
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
        await ctx.message.add_reaction("☑")

    @root_bot.command(name="disable", version=1)
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
        await ctx.message.add_reaction("☑")

    @root_bot.command(name="close", version=1)
    async def root_bot_close(self, ctx: commands.Context):
        """Closes the bot."""
        await ctx.message.add_reaction("👋")
        await self.bot.close