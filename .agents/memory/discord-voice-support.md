---
name: Discord voice support
description: Dependency required for Alythia voice-channel commands.
---

Discord voice connections require PyNaCl in addition to discord.py; without it the bot can connect to Gateway but voice commands fail and discord.py logs that voice is unsupported.

**Why:** Voice support is an optional dependency and is not installed by the base discord.py package.

**How to apply:** Keep PyNaCl in the Python project dependencies whenever voice-channel features are enabled.