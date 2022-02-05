from discord.ext import commands

owner: list
settings = {"folder": {"path_to_file": None, "root_folder": None}, "kwargs": {"separator": "=", "format": "%(key)s%(sep)s%(word)s"}, "owners": None}


def set_settings(bot: commands.Bot):
    global owner
    if not [bot.owner_ids, bot.owner_id]:
        raise Exception("For security reasons, please set (a) owner id(s) when creating your bot object and using the dev module.")
    owner = bot.owner_ids or [bot.owner_id]


def get_owner():
    return owner