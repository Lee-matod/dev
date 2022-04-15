from discord.ext import commands
from typing import Optional, Dict

from dev.utils.baseclass import root

settings = {
    "folder": {
        "path_to_file": "",   # type: str
        "root_folder": ""  # type: str
    },

    "source": {
        "filename": "",  # type: str
        "use_file": False,  # type: bool
    },

    "owners": []  # type: list, tuple, set
}

owner: list
cogs: Dict[str, commands.Cog] = {}


def set_settings(bot: commands.Bot):
    global owner
    if not [bot.owner_ids, bot.owner_id, settings["owners"]]:
        raise Exception("For security reasons, please set owner id(s) when using the dev module.")
    owner = bot.owner_ids or [bot.owner_id]
    check_types()


def check_types():
    setting_types = {"folder": {"path_to_file": str, "root_folder": str}, "source": {"filename": str, "use_file": bool}, "owners": (list, tuple, set)}
    for module in setting_types:
        if module == "owners":
            if not isinstance(settings["owners"], (list, tuple, set)):
                raise ValueError(f"invalid type for 'settings[{module}]'. Expected {', '.join(sett.__name__ for sett in setting_types[module])} but received {type(settings['owners']).__name__}")
        else:
            for setting in setting_types[module]:
                if not isinstance(settings[module][setting], setting_types[module][setting]):
                    raise ValueError(f"invalid type for 'settings[{module}][{setting}]'. Expected {setting_types[module][setting].__name__} but received {type(settings[module][setting]).__name__}")


def get_owner():
    return owner


def set_cogs(**kwargs):
    global cogs
    for name, inst in kwargs.items():
        cogs[name] = inst


async def setup_(bot: commands.Bot, *args):
    for ext in args:
        try:
            await bot.load_extension(ext)
        except commands.ExtensionAlreadyLoaded:
            await bot.unload_extension(ext)
            await bot.load_extension(ext)

    for cmd, parent_name in root._add_parent.items():
        parent: Optional[commands.Group] = bot.get_command(parent_name)
        parent.add_command(cmd)
        bot.remove_command(cmd.name)
