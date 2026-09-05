import os


TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DATABASE_PATH = os.getenv("DATABASE_PATH", "discord_bot/alythia.sqlite3")
BOT_NAME = "Alythia"

COLOUR_PRIMARY = 0x8B5CF6
COLOUR_SUCCESS = 0x22C55E
COLOUR_WARNING = 0xF59E0B
COLOUR_DANGER = 0xEF4444
COLOUR_MUTED = 0x64748B


def missing_configuration() -> str | None:
    if not TOKEN:
        return "السر DISCORD_BOT_TOKEN غير موجود في Replit Secrets."
    return None