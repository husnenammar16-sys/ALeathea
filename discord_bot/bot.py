from __future__ import annotations

import logging
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import discord
from discord import app_commands
from discord.ext import commands

from .config import TOKEN, missing_configuration
from .database import Database
from .cogs import (
    autorole,
    automod,
    custom,
    economy,
    fun,
    general,
    giveaways,
    levels,
    logs,
    moderation,
    reaction_roles,
    suggestions,
    tickets,
    welcome,
    prefix,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("alythia")


def verify_token_application(token: str) -> None:
    request = Request(
        "https://discord.com/api/v10/users/@me",
        headers={"Authorization": f"Bot {token}"},
    )
    try:
        with urlopen(request, timeout=10) as response:
            identity = json.loads(response.read().decode("utf-8"))
        logger.info(
            "التوكن مرتبط بالبوت: %s (ID: %s)",
            identity.get("username", "غير معروف"),
            identity.get("id", "غير معروف"),
        )
    except HTTPError as error:
        logger.error("تعذر التحقق من التوكن. رمز Discord: %s", error.code)
    except (URLError, TimeoutError) as error:
        logger.error("تعذر الوصول إلى Discord للتحقق من التوكن: %s", error)


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
        await economy.setup(self, self.database)
        await levels.setup(self, self.database)
        await fun.setup(self, self.database)
        await giveaways.setup(self, self.database)
        await reaction_roles.setup(self, self.database)
        await automod.setup(self, self.database)
        await custom.setup(self, self.database)
        await prefix.setup(self, self.database)
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

    async def on_command_error(
        self, context: commands.Context[commands.Bot], error: commands.CommandError
    ) -> None:
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingPermissions):
            message = "ليس لديك صلاحية لاستخدام هذا الأمر."
        elif isinstance(error, commands.MissingRequiredArgument):
            message = f"البيانات ناقصة. الاستخدام الصحيح: `!{context.command}` مع كل الخيارات المطلوبة."
        elif isinstance(error, commands.BadArgument):
            message = "البيانات المدخلة غير صحيحة. تأكد من منشن العضو أو كتابة الرقم بشكل صحيح."
        elif isinstance(error, commands.NoPrivateMessage):
            message = "هذا الأمر يعمل داخل السيرفر فقط."
        else:
            logger.exception("حدث خطأ في أمر البريفكس", exc_info=error)
            message = "حدث خطأ غير متوقع أثناء تنفيذ الأمر."
        await context.send(message, delete_after=8)


def main() -> None:
    error = missing_configuration()
    if error:
        raise RuntimeError(error)
    verify_token_application(TOKEN)
    database = Database()
    bot = AlythiaBot(database)
    try:
        bot.run(TOKEN)
    finally:
        database.close()


if __name__ == "__main__":
    main()