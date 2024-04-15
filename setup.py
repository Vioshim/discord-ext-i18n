# Copyright (C) 2024 Vioshim (original author: Avery)
#
# This file is part of discord-ext-i18n.
#
# discord-ext-i18n is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# discord-ext-i18n is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with discord-ext-i18n.  If not, see <http://www.gnu.org/licenses/>.


from os import path

from setuptools import setup

DESCRIPTION_PATH = path.join(path.abspath(path.dirname(__file__)), "README.md")
with open(DESCRIPTION_PATH, encoding="utf-8") as f:
    long_description = f.read()

REQUIREMENTS_PATH = path.join(path.abspath(path.dirname(__file__)), "requirements.txt")
with open(REQUIREMENTS_PATH, encoding="utf-8") as f:
    requirements = f.read()


setup(
    name="discord-ext-i18n",
    author="Vioshim",
    url="https://github.com/Vioshim/discord-ext-i18n",
    keywords=["discord.py", "discord", "i18n", "asyncio"],
    version="1.0.0",
    packages=["discord.ext.i18n"],
    include_package_data=True,
    license="GNU General Public License v3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    description="I18n extension for Discord.py (Py18n Fork)",
    python_requires=">=3.10.0",
    install_requires=requirements,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
)
