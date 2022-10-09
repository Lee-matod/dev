import re
from setuptools import setup

with open("dev/__init__.py") as file:
    version = re.search(r'__version__ = \"(\d+\.\d+\.\d(a|b|rc)?)\"', file.read()).group(1)
    if not version:
        raise RuntimeError("version is not set")

if version.endswith(("a", "b", "rc")):
    try:
        import subprocess
        count, err = subprocess.Popen(
            ["git", "rev-list", "--count", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).communicate()
        if count:
            commit, err = subprocess.Popen(
                ["git", "rev-parse", "--short", "HEAD"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            ).communicate()
            if commit:
                version += count.decode("utf-8").strip() + "+g" + commit.decode("utf-8").strip()
            else:
                version += count.decode("utf-8").strip()
    except Exception:  # noqa
        pass

with open("requirements.txt") as file:
    requirements = file.readlines()[1:]  # exclude discord.py

with open("README.md", "r") as file:
    readme = file.read()

extras_require = {
    "test": [
        "pytest",
        "pytest-asyncio"
    ]
}

setup(
    name="dev",
    author="Lee-matod",
    url="https://github.com/Lee-matod/dev",
    version=version,
    packages=["dev", "dev.config", "dev.experimental", "dev.misc", "dev.utils"],
    license="Apache 2.0",
    description="A debugging, testing and editing cog for discord.py",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    install_requires=requirements,
    dependency_links=["git+ssh://git@github.com/Rapptz/discord.py.git#egg=discord"],  # tysm DJJ!
    python_requires=">=3.8.0"
)
