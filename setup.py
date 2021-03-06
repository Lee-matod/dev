from setuptools import setup

with open("requirements.txt") as file:
    requirements = file.read().splitlines()[1:]  # exclude discord.py

with open("README.md", "r") as file:
    readme = file.read()

setup(
    name="dev",
    author="Lee-matod",
    url="https://github.com/Lee-matod/dev",
    version="1.0.0a",
    packages=["dev", "dev.config", "dev.experimental", "dev.misc", "dev.utils"],
    license="Apache 2.0",
    description="A debugging, testing and editing cog for discord.py",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    install_requires=requirements,
    dependency_links=["git+ssh://git@github.com/Rapptz/discord.py.git#egg=discord"],
    python_requires=">=3.8.0",
)
