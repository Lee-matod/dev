from unittest.mock import Mock

import discord
import pytest
from discord.ext import commands

from dev import Dev, Settings

ctx = Mock()


@commands.command()
async def mock_command(_):
    pass


mock_command.cog = commands.Cog()


@pytest.mark.asyncio
async def test_owner_ids():
    with pytest.raises(commands.ExtensionFailed):
        #  No owner ID
        bot = commands.Bot(command_prefix="?", intents=discord.Intents.all())
        await bot.load_extension("dev")
        await bot.unload_extension("dev")
    bot = commands.Bot(command_prefix="?", intents=discord.Intents.all(), owner_id=123)
    await bot.load_extension("dev")
    await bot.unload_extension("dev")
    bot = commands.Bot(command_prefix="?", intents=discord.Intents.all(), owner_ids={123})
    await bot.load_extension("dev")
    await bot.unload_extension("dev")

    #  We don't test Settings.owners because it just fails, but when actually implemented, it doesn't.


@pytest.mark.asyncio
async def test_cog_check():
    bot = commands.Bot(command_prefix="?", intents=discord.Intents.all(), owner_id=123)
    await bot.load_extension("dev")
    cog: Dev = bot.get_cog("Dev")
    assert cog is not None
    root_command = bot.get_command("dev")
    assert root_command is not None

    #  Non-dev command
    ctx.command = mock_command
    allowed = await cog.cog_check(ctx)
    assert allowed is True

    #  dev command and non-owner
    with pytest.raises(commands.NotOwner):
        ctx.command = root_command
        ctx.command.cog = cog
        allowed = await cog.cog_check(ctx)

    #  dev command and owner
    ctx.author.id = 123
    allowed = await cog.cog_check(ctx)
    assert allowed is True

    #  Global dev command and non-owner, with global commands enabled
    Settings.allow_global_uses = True
    ctx.author.id = 1234
    allowed = await cog.cog_check(ctx)
    assert allowed is True
