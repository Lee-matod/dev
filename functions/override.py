import discord

from discord.ext import commands

from dev.utils.functs import is_owner


class RootOverrideBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(name="override")
    @is_owner()
    async def root_override(self, ctx: commands.Context):
        return

    @root_override.command(name="bot")
    @is_owner()
    async def root_override_bot(self, ctx: commands.Context, func: str, *, value: str):
        if func == "prefix":
            self.bot.command_prefix = value
            return await ctx.message.add_reaction("✅")
        if func == "owners":
            new_owners = []
            if "self" in value:
                new_owners.append(self.bot.owner_ids or self.bot.owner_id)
                value = value.replace("self", "")
            owners = ""
            for i in value:
                if i.isdigit():
                    owners += i
                else:
                    print(owners)
                    print(value)
                    if not owners[-1].isdigit():
                        continue
                    owners += " "
            owners = owners.split()
            for o in owners:
                new_owners.append(int(o))
            print(set(new_owners))
        return await ctx.message.add_reaction("❓")

    @root_override.command(name="file")
    async def root_override_file(self, ctx: commands.Context, line):
        pass

def setup(bot):
    bot.add_cog(RootOverrideBot(bot))