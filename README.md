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
A language can be initialized like this:
```python
french = Language("fr", "French", {
    "hello": "Bonjour",
    "goodbye": "Au revoir",
    "francais": "Français"
})
```

But you may want to store languages seperately and create them as follows:
```python
import json
french = Language("fr", translations=json.load(open("fr.json")))
```

### Base I18n class
When setting up the i18n class, we need to setup our languages and declare a fallback language:
```python
i18n = I18n([
    Language("en", translations={
        "hello": "Hello",
        "goodbye": "Goodbye",
        "english": "English"
    }),
    Language("fr", translations={
        "hello": "Bonjour",
        "goodbye": "Au revoir",
        "francais": "Français"
    }),
], fallback="en")
```

`i18n` will now fallback to english if it can't find a translation for other languages.
```python
>>> i18n.get_text("hello", "en")
'Hello'
>>> i18n.get_text("hello", "fr")
'Bonjour'
>>> # "english" is not a listed translation in the French locale, so we revert to english
>>> i18n.get_text("english", "fr")
'English'
>>> # However we can make it not fallback, but this will throw an error if the translation isn't found
>>> i18n.get_text("english", "fr", should_fallback=False) 
Traceback (most recent call last):
  ...      
discord.ext.i18n.InvalidTranslationKeyError: 'Translation foo not found for en!'
```

### Discord
For Discord.py, we can use the extension `py18n.extension.I18nExtension`. Setup your bot as you would usually, and then run `i18n.init_bot` as follows.

```python
from discord import Intents
from discord.ext import commands
from discord.ext.i18n import I18nExtension

# Make our bot
bot = commands.Bot("prefix", intents=Intents.default())

# Setup similarly to the usual class
i18n = I18nExtension([
    Language("en", "English", {
        "hello": "Hello",
        "goodbye": "Goodbye",
        "english": "English"
    }),
    Language("fr", "French", {
        "hello": "Bonjour",
        "goodbye": "Au revoir",
        "francais": "Français"
    }),
], fallback="en")

# Setup the bot by giving it a function to get the user's locale.
# This could potentially refer to a database or other file.
# Anything you want!
# Otherwise, it will always be the fallback locale.
async def get_locale(ctx: commands.Context):
    preferences = {
       301736945610915852: "fr"
    }
    return preferences.get(ctx.author.id, "en")

# Set it up!
i18n.init_bot(bot, get_locale)

@bot.hybrid_command()
async def hello(ctx: commands.Context):
    await ctx.reply(i18n.contextual_get_text("hello"))
```

This is all good, but because of our line `i18n.init_bot(bot, get_locale)`, we can shorten things.

This function adds a pre-invoke hook that sets the language based on the result of `get_locale`. The `contextually_get_text` function is also exposed as `py18n.extension._`, and it is a `classmethod`.

We can change it by adding the following import and change our function:
```python
from discord.ext.i18n import _

# ...

@bot.hybrid_command()
async def hello(ctx: commands.Context):
    await ctx.reply(_("hello"))
```

There, much tidier!
- The `_` function considers the current context and uses the correct locale by default.
- When initializing any `I18nExtension`, as we did earlier, it becomes the default i18n instance. The default instance is used by `_` and `contextually_get_text`.

## Issues
If you encounter any problems, check out [current issues](https://github.com/Vioshim/discord-ext-i18n/issues) or [make a new issue](https://github.com/Vioshim/discord-ext-i18n/issues/new).

## Notes
- This project is a fork of [Py18n](https://github.com/starsflower/py18n)
- Feel free to contribute! This is released under the GLP-3 license. (If you suggest another license, make an issue suggesting).
