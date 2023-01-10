import re
from setuptools import setup

with open("dev/__init__.py") as file:
    version = re.search(r'__version__ = \"(\d+\.\d+\.\d(a|b|rc)?)\"', file.read())
    if version is None:
        raise RuntimeError("version is not set")
    version = version.group(1)

if version.endswith(("a", "b", "rc")):
    try:
        import subprocess

        count, _ = subprocess.Popen(
            ["git", "rev-list", "--count", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).communicate()
        commit, _ = subprocess.Popen(
            ["git", "rev-parse", "--short", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).communicate()
        if count:
            version += count.decode("utf-8").strip()
        if commit:
            version += f"+g{commit.decode('utf-8')}".strip()
    except Exception:  # noqa
        pass

with open("requirements.txt") as file:
    requirements = file.readlines()

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
    packages=["dev", "dev.components", "dev.config", "dev.experimental", "dev.misc", "dev.utils"],
    license="MIT",
    description="A debugging, testing and editing cog for discord.py",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.8.0",
    extras_require={"test": ["pytest", "pytest-asyncio"]}
)
