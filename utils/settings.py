from discord.ext import commands
from typing import Union

settings = {
    "folder": {
        "path_to_file": None,   # type: str
        "root_folder": None  # type: str
    },

    "kwargs": {
        "separator": "=",  # type: str
        "format": "%(key)s%(sep)s%(word)s"  # type: str
    },

    "source": {
        "filename": None,  # type: str
        "use_file": False,  # type: bool
        "not_dev_cmd": "./",  # type: str
        "show_path": False  # type: bool
    },

    "file": {
        "use_file": False,  # type: bool
        "/": "/",  # type: str
        "show_path": True  # type: bool
    },

    "owners": None  # type: Union[list, tuple, set]
}
owner: list


def set_settings(bot: commands.Bot):
    global owner
    if not [bot.owner_ids, bot.owner_id]:
        raise Exception("For security reasons, please set (a) owner id(s) when creating your bot object and using the dev module.")
    owner = bot.owner_ids or [bot.owner_id]


def get_owner():
    return owner