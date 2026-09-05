---
name: Discord voice support
description: Dependency required for Alythia voice-channel commands.
---

Discord voice connections require PyNaCl and davey in addition to discord.py; without either optional dependency the bot can connect to Gateway but voice commands fail.

**Why:** Voice support and its current transport are optional dependencies and are not installed by the base discord.py package.

**How to apply:** Keep PyNaCl in the Python project dependencies whenever voice-channel features are enabled.