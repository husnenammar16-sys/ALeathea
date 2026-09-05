from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from .config import TOKEN, missing_configuration
from .database import Database
from .cogs import autorole, general, logs, moderation, suggestions, tickets, welcome

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("alythia")


class AlythiaBot(commands.Bot):
    def __init__(self, database: Database) -> None:
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
        )
        self.database = database

    async def setup_hook(self) -> None:
        await general.setup(self, self.database)
        await logs.setup(self, self.database)
        await welcome.setup(self, self.database)
        await moderation.setup(self, self.database)
        await autorole.setup(self, self.database)
        await tickets.setup(self, self.database)
        await suggestions.setup(self, self.database)
        synced = await self.tree.sync()
        logger.info("تم تسجيل %s أمر Slash.", len(synced))

    async def on_ready(self) -> None:
        if self.user:
            logger.info("تم تشغيل Alythia باسم %s في %s سيرفر.", self.user, len(self.guilds))

    async def on_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        original = getattr(error, "original", error)
        if isinstance(error, app_commands.errors.MissingPermissions):
            message = "ليس لديك صلاحية لاستخدام هذا الأمر."
        elif isinstance(original, discord.Forbidden):
            message = "لا أملك الصلاحيات الكافية لتنفيذ هذا الأمر."
        elif isinstance(original, discord.HTTPException):
            message = "حدث خطأ من Discord. تأكد من صلاحيات البوت وحاول مرة أخرى."
        else:
            logger.exception("حدث خطأ في أمر Slash", exc_info=original)
            message = "حدث خطأ غير متوقع. تم تسجيل المشكلة للإدارة."

        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)


def main() -> None:
    error = missing_configuration()
    if error:
        raise RuntimeError(error)
    database = Database()
    bot = AlythiaBot(database)
    try:
        bot.run(TOKEN)
    finally:
        database.close()


if __name__ == "__main__":
    main()