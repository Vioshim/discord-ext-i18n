<!--
Copyright (C) 2024 Vioshim (original author: Avery)

This file is part of discord-ext-i18n.

discord-ext-i18n is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

discord-ext-i18n is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with discord-ext-i18n.  If not, see <http://www.gnu.org/licenses/>.

-->

# discord-ext-i18n
This is a open source fork of Py18n whose purpose is to make commands translations easier in discord.py bots.


## Installation
To install the package to your Python installation, clone the repository locally then run the following command in the repository's directory
```bash
py setup.py install
```

You can now use the library!

## Usage

### Setting up languages

This library is meant to be flexible when it comes to using i18n, by default it'll try to load from the folder `locale`.

In this example, we'll create a file `locale/en-US.json`
which will have the following information.

```json
{
    "Hello": "Hello there, {{author}}",
    "commands": {
        "hello": {
            "name": "hello",
            "description": "A command to say hello",
            "params": {
                "name": "user",
                "description": "User that you want to greet"
            },
        }
    }
}

```

### Installing in Discord.py
It's important in this step to install `I18nTranslator`, this class can be inherited and adjusted as needed.
By default it has a basic setup which works in the following way.

```python
from discord import Intents, Member
from discord.ext import commands
from discord.ext.i18n import I18nTranslator, _

class Translator(I18nTranslator):
    fallback = Locale.american_english

    async def get_locale(self, ctx: commands.Context) -> Locale:
        preferences = {678374009045254198: "es-419"}
        return preferences.get(ctx.author.id, self.fallback)

class Bot(commands.Bot):
    async def setup_hook(self):
        await self.tree.set_translator(Translator(bot))

bot = Bot("prefix", intents=Intents.default())

@bot.hybrid_command()
async def hello(ctx: commands.Context, user: Member = commands.Author):
    await ctx.reply(_("Hello", author=user.mention))
```

## Issues
If you encounter any problems, check out [current issues](https://github.com/Vioshim/discord-ext-i18n/issues) or [make a new issue](https://github.com/Vioshim/discord-ext-i18n/issues/new).

## Notes
- This project is a fork of [Py18n](https://github.com/starsflower/py18n)
- Project example that does make use of this library [D-Proxy](https://github.com/Vioshim/DProxy-i18n)
- Feel free to contribute! This is released under the GLP-3 license. (If you suggest another license, make an issue suggesting).