import discord

from discord.ext import commands
from typing import Optional, Union

from dev.utils.baseclass import root
from dev.utils.functs import is_owner, generate_ctx


class ReinvokeFlags(commands.FlagConverter):
    has_: Optional[str] = commands.flag(name="has", default=None)
    startswith_: Optional[str] = commands.flag(name="startswith", default=None)
    endswith_: Optional[str] = commands.flag(name="endswith", default=None)


class RootInvoke(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @root.command(name="execute", aliases=["exec", "execute!", "exec!"], parent="dev", version=1)
    @is_owner()
    async def root_execute(self, ctx: commands.Context, attrs: commands.Greedy[Union[discord.Member, discord.TextChannel, discord.Thread]], *, command_attr: str):
        """Execute a command with custom attributes.
        Attributes support types are `discord.Member`, `discord.TextChannel` and `discord.Thread`. These will override the current context, thus executing the command as another user or place.
        Command checks can be optionally disabled by adding an exclamation mark at the end of the `execute` command.
        """
        kwargs = {"content": f"{ctx.prefix}{command_attr}", "author": ctx.author, "channel": ctx.channel}
        for attr in attrs:
            if isinstance(attr, discord.Member):
                kwargs["author"] = attr
            elif isinstance(attr, discord.TextChannel) or isinstance(attr, discord.Thread):
                kwargs["channel"] = attr
        context: commands.Context = await generate_ctx(ctx, **kwargs)
        if not context.command:
            return await ctx.send(f"Command not found.")
        if ctx.invoked_with.endswith("!"):
            return await context.command.reinvoke(context)
        await context.command.invoke(context)

    @root.command(name="reinvoke", parent="dev", version=1)
    @is_owner()
    async def root_reinvoke(self, ctx: commands.Context, skip_message: Optional[int] = 0, author: Optional[discord.Member] = None, *, flags: ReinvokeFlags):
        """Reinvoke the last command that was executed.
        By default, it will try to get the last command that was executed excluding `dev reinvoke` (for obvious reasons).
        If `Message.reference` is not of type `None`, then it will try to reinvoke the command that was executed in the reference. This method of reinvocation ignores all other options and flags.
        **Flag arguments:**
        `has`: _str_ = Check if the message has a specific sequence of characters. Defaults to _None_.
        `startswith`: _str_ = Check if the message startswith a specific characters. Defaults to _None_.
        `endswith`: _str_ = Check if the message endswith a specific characters. Defaults to _None_.
        """
        if ctx.message.reference:
            if ctx.message.reference.resolved.content.startswith(ctx.prefix):
                context: commands.Context = await self.bot.get_context(ctx.message.reference.resolved)
                return await context.command.reinvoke(context)
            return await ctx.send("No command found in the message reference.")
        author = author or ctx.author
        c = 0
        async for message in ctx.channel.history(limit=100):
            if message.author == author:
                if message.content.startswith(f"{ctx.prefix}dev reinvoke"):
                    skip_message += 1
                    c += 1
                    continue
                if c == skip_message:
                    if flag_checks(message, flags):
                        context: commands.Context = await generate_ctx(ctx, ctx.author, ctx.channel, content=message.content)
                        return await context.command.reinvoke(context)
                c += 1
        await ctx.send("Unable to find any messages matching the given arguments.")


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


async def setup(bot):
    await bot.add_cog(RootInvoke(bot))
