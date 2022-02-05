from discord.ext import commands


def setup_(bot: commands.Bot, **kwargs):
    ext: list = kwargs.pop("extentions", False)
    cmds: list = kwargs.pop("commands", False)
    if ext:
        for e in ext:
            bot.load_extension(e)
    if cmds:
        get_and_set_root(bot, cmds)


def get_and_set_root(bot: commands.Bot, cmds):
    for cmd in cmds:
        root = bot.get_command("dev")
        command = bot.get_command(cmd)
        root.add_command(command)
        bot.remove_command(cmd)