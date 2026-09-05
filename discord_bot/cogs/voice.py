from __future__ import annotations

import asyncio
from typing import cast

import discord
from discord import app_commands
from discord.ext import commands

from ..utils import embed

STAY_DURATION_SECONDS = 24 * 60 * 60


class Voice(commands.Cog):
    voice = app_commands.Group(name="voice", description="التحكم بوجود البوت في الروم الصوتي")

    def __init__(self, bot: commands.Bot, database: object) -> None:
        self.bot = bot
        self.disconnect_tasks: dict[int, asyncio.Task[None]] = {}

    async def _disconnect_later(self, guild_id: int, voice_client: discord.VoiceClient) -> None:
        try:
            await asyncio.sleep(STAY_DURATION_SECONDS)
            if voice_client.is_connected():
                await voice_client.disconnect(force=True)
        except asyncio.CancelledError:
            raise
        finally:
            self.disconnect_tasks.pop(guild_id, None)

    def _start_timer(self, guild_id: int, voice_client: discord.VoiceClient) -> None:
        old_task = self.disconnect_tasks.pop(guild_id, None)
        if old_task:
            old_task.cancel()
        self.disconnect_tasks[guild_id] = asyncio.create_task(
            self._disconnect_later(guild_id, voice_client)
        )

    async def _join_channel(
        self, guild: discord.Guild, channel: discord.abc.GuildChannel
    ) -> discord.VoiceClient:
        if not isinstance(channel, (discord.VoiceChannel, discord.StageChannel)):
            raise ValueError("ليس هذا رومًا صوتيًا.")
        current = guild.voice_client
        if current and current.is_connected():
            if current.channel != channel:
                await current.move_to(channel)
            voice_client = current
        else:
            voice_client = cast(discord.VoiceClient, await channel.connect())
        self._start_timer(guild.id, voice_client)
        return voice_client

    async def _leave_guild(self, guild: discord.Guild) -> bool:
        task = self.disconnect_tasks.pop(guild.id, None)
        if task:
            task.cancel()
        if not guild.voice_client:
            return False
        await guild.voice_client.disconnect(force=True)
        return True

    @voice.command(name="join", description="إدخال البوت إلى رومك الصوتي لمدة 24 ساعة")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def join(self, interaction: discord.Interaction) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("هذا الأمر يعمل داخل السيرفر فقط.", ephemeral=True)
            return
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message(
                "ادخل رومًا صوتيًا أولًا ثم استخدم الأمر.",
                ephemeral=True,
            )
            return
        try:
            voice_client = await self._join_channel(
                interaction.guild,
                interaction.user.voice.channel,
            )
        except (discord.ClientException, discord.Forbidden, discord.HTTPException, ValueError):
            await interaction.response.send_message(
                "تعذر دخول الروم الصوتي. تأكد أن لدي صلاحية **Connect** في الروم.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            embed=embed(
                "تم دخول الروم الصوتي",
                f"دخلت إلى **{voice_client.channel.name}** وسأبقى فيه لمدة **24 ساعة**.\n"
                "استخدم `/voice leave` لإخراجي قبل انتهاء المدة.",
            ),
            ephemeral=True,
        )

    @voice.command(name="leave", description="إخراج البوت من الروم الصوتي")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def leave(self, interaction: discord.Interaction) -> None:
        if not interaction.guild:
            await interaction.response.send_message("هذا الأمر يعمل داخل السيرفر فقط.", ephemeral=True)
            return
        left = await self._leave_guild(interaction.guild)
        await interaction.response.send_message(
            "خرجت من الروم الصوتي." if left else "أنا لست داخل روم صوتي حاليًا.",
            ephemeral=True,
        )

    @commands.command(name="join", aliases=["دخول"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def prefix_join(self, ctx: commands.Context[commands.Bot]) -> None:
        if not isinstance(ctx.author, discord.Member) or not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("ادخل رومًا صوتيًا أولًا ثم استخدم `!join`.", delete_after=8)
            return
        try:
            voice_client = await self._join_channel(ctx.guild, ctx.author.voice.channel)
        except (discord.ClientException, discord.Forbidden, discord.HTTPException, ValueError):
            await ctx.send("تعذر دخول الروم. تأكد أن لدي صلاحية Connect.", delete_after=8)
            return
        await ctx.send(
            embed=embed(
                "تم دخول الروم الصوتي",
                f"دخلت إلى **{voice_client.channel.name}** وسأبقى فيه لمدة **24 ساعة**.",
            )
        )

    @commands.command(name="leave", aliases=["خروج"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def prefix_leave(self, ctx: commands.Context[commands.Bot]) -> None:
        left = await self._leave_guild(ctx.guild)
        await ctx.send("خرجت من الروم الصوتي." if left else "أنا لست داخل روم صوتي حاليًا.", delete_after=8)

    def cog_unload(self) -> None:
        for task in self.disconnect_tasks.values():
            task.cancel()
        self.disconnect_tasks.clear()


async def setup(bot: commands.Bot, database: object) -> None:
    await bot.add_cog(Voice(bot, database))