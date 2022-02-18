from discord.ext import commands

from dev.utils.baseclass import add_parents


def setup_(bot: commands.Bot, *args):
    for ext in args:
        bot.load_extension(ext)

    for cmd in add_parents:
        parent: commands.Group = bot.get_command(add_parents[cmd])
        parent.add_command(cmd)
        bot.remove_command(cmd.name)

