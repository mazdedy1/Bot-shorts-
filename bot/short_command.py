import asyncio
import os
from pathlib import Path

import discord
from discord import app_commands

from services.downloader import download_video


def register_short_command(tree: app_commands.CommandTree) -> None:
    @tree.command(name="short", description="Buat video Shorts dari URL YouTube.")
    @app_commands.describe(url="URL video YouTube yang akan diproses")
    async def short(interaction: discord.Interaction, url: str) -> None:
        embed = discord.Embed(title="SHORTS MAKER", color=0x5865F2)
        embed.add_field(name="Status", value="Permintaan diterima.", inline=False)
        embed.add_field(name="Sumber video", value=url[:1000], inline=False)
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        async def update(status: str, color: int = 0x5865F2) -> None:
            embed.color = color
            embed.set_field_at(0, name="Status", value=status, inline=False)
            await message.edit(embed=embed)

        try:
            await update("Sedang mengunduh video...")
            work_dir = Path(os.getenv("WORK_DIR", "work")) / str(interaction.id)
            work_dir.mkdir(parents=True, exist_ok=True)
            video_path, metadata = await asyncio.to_thread(download_video, url, work_dir)
            embed.add_field(name="Download", value="Selesai.", inline=False)
            embed.add_field(name="Video", value=f"{metadata.get('title', 'Video')[:250]}\nDurasi sumber: {metadata.get('duration', 0)} detik", inline=False)
            embed.add_field(name="Tahap berikutnya", value="Fondasi download sudah berjalan. Integrasi AI Director, TTS, dan FFmpeg Editor masih dalam tahap pembangunan.", inline=False)
            await message.edit(embed=embed)
        except Exception:
            await update("Proses gagal. Periksa URL, batas durasi, dan log GitHub Actions.", 0xED4245)


