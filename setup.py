from setuptools import setup

with open("README.md", "r") as file:
    readme = file.read()

packages = [
    "dev"
]

setup(name="dev",
      author="Lee-matod",
      url="https://github.com/Lee-matod/dev",
      version="1.0.0",
      packages=packages,
      license="Apache 2.0",
      description="A debugging, testing and editing cog for discord.py",
      long_description=readme,
      long_description_content_type="text/markdown",
      include_package_data=True,
      python_requires=">=3.9.0",
)
