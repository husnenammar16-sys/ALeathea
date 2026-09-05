from __future__ import annotations

import random
import time

import discord
from discord import app_commands
from discord.ext import commands

from ..database import Database
from ..utils import embed, member_name


class Levels(commands.Cog):
    def __init__(self, bot: commands.Bot, database: Database) -> None:
        self.database = database
        self.cooldowns: dict[tuple[int, int], float] = {}

    @app_commands.command(name="rank", description="عرض مستواك أو مستوى عضو")
    @app_commands.describe(member="عضو اختياري")
    async def rank(self, interaction: discord.Interaction, member: discord.Member | None = None) -> None:
        target = member or interaction.user
        row = self.database.get_level(interaction.guild_id, target.id)
        needed = (int(row["level"]) + 1) * 100
        card = embed(
            f"مستوى {member_name(target)}",
            f"المستوى الحالي: **{row['level']}**\nالخبرة: **{row['xp']} / {needed}**",
        )
        card.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=card)

    @app_commands.command(name="leaderboard", description="عرض ترتيب المستويات")
    async def leaderboard(self, interaction: discord.Interaction) -> None:
        rows = self.database.level_leaderboard(interaction.guild_id)
        lines = [
            f"**{index}.** <@{row['user_id']}> — المستوى {row['level']} ({row['xp']} XP)"
            for index, row in enumerate(rows, start=1)
        ]
        await interaction.response.send_message(
            embed=embed("ترتيب المستويات", "\n".join(lines) or "لا توجد مستويات بعد.")
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if not message.guild or message.author.bot:
            return
        key = (message.guild.id, message.author.id)
        now = time.monotonic()
        if now - self.cooldowns.get(key, 0) < 30:
            return
        self.cooldowns[key] = now
        row_before = self.database.get_level(message.guild.id, message.author.id)
        row_after = self.database.add_xp(message.guild.id, message.author.id, random.randint(10, 25))
        if row_after["level"] > row_before["level"]:
            await message.channel.send(
                f"مبروك {message.author.mention}! وصلت إلى المستوى **{row_after['level']}**."
            )


async def setup(bot: commands.Bot, database: Database) -> None:
    await bot.add_cog(Levels(bot, database))