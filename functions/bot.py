import discord

from collections.abc import Iterator
from discord.ext import commands

from dev.utils.functs import is_owner


class Frames:
    def __init__(self, bot: commands.Bot, *args):
        self.bot = bot
        self.args = args

    @property
    def intents(self):
        return [self.intents.__name__.title(), dict(self.bot.intents)]

    @property
    async def owners(self):
        return [self.owners.__name__.title(), [await self.bot.fetch_user(o) for o in self.bot.owner_ids or self.bot.owner_id]]


class RootBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(name="bot", invoke_without_command=True)
    @is_owner()
    async def root_bot(self, ctx: commands.Context):
        pass

    @root_bot.command(name="check")
    @is_owner()
    async def root_bot_check(self, ctx: commands.Context, checks, value=None):
        if not value:
            valid_checks = ["guilds", "owners", "commands", "self", "~"]
            if checks not in valid_checks:
                return await ctx.message.add_reaction("❓")

    def add_field(self, embed: discord.Embed, value, **kwargs):
        self.bot_frames = {
            "all": {
                "intents": {intents: dict(self.bot.intents)[intents] for intents in dict(self.bot.intents)},
                "bot": self.bot.user.mention,
                "description": self.bot.description,
                "id": self.bot.user.id,
                "guilds": len(self.bot.guilds),
                "channels": len([guild.channels for guild in self.bot.guilds]),
                "users": len(self.bot.users),
                "prefix": self.bot.command_prefix,
                "commands": len(self.bot.commands),
                "extensions": len(self.bot.extensions),
                "owners": ', '.join(f"<@!{owner}>" for owner in self.bot.owner_ids or self.bot.owner_id),
                "latency": self.bot.latency,
                "activity": self.bot.activity,
                "flags": {flags: dict(self.bot.application_flags)[flags] for flags in dict(self.bot.application_flags)}
            },
            "owners": {

            },
            "guilds": {

            },
            "commands": {

            },
            "extensions": {

            }
        }
        if not value:
            for frame in self.bot_frames["all"]:
                if isinstance(frame, Iterator):
                    val = []
                    for i in self.bot_frames["all"][frame]:
                        val.append(f"`{i}`: `{self.bot_frames['all'][frame][i]}`")
                    embed.add_field(name=frame, value=', '.join(val), inline=False)
                    continue
                embed.add_field(name=frame, value=self.bot_frames["all"][frame])


def setup(bot):
    bot.add_cog(RootBot(bot))