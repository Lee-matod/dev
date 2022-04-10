from discord.ext import commands
from typing import Optional, Union

from dev.utils.baseclass import root

settings = {
    "folder": {
        "path_to_file": "",   # type: str
        "root_folder": ""  # type: str
    },

    "kwargs": {
        "separator": "=",  # type: str
        "format": "%(key)s%(sep)s%(word)s"  # type: str
    },

    "source": {
        "filename": "",  # type: str
        "use_file": False,  # type: bool
        "not_dev_cmd": "./",  # type: str
        "show_path": False  # type: bool
    },

    "file": {
        "use_file": False,  # type: bool
        "/": "/",  # type: str
        "show_path": True  # type: bool
    },
    "owners": []  # type: list, tuple, set
}
owner: list


def set_settings(bot: commands.Bot):
    global owner
    if not [bot.owner_ids, bot.owner_id]:
        raise Exception("For security reasons, please set (a) owner id(s) when creating your bot object and using the dev module.")
    owner = bot.owner_ids or [bot.owner_id]
    check_types()


def check_types():
    setting_types = {"folder": {"path_to_file": str, "root_folder": str}, "kwargs": {"separator": str, "format": str}, "source": {"filename": str, "use_file": bool, "not_dev_cmd": str, "show_path": bool}, "file": {"use_file": bool, "/": str, "show_path": bool}, "owners": (list, tuple, set)}
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
