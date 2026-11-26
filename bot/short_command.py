import asyncio
import os
from pathlib import Path

import discord
from discord import app_commands

from ai.director import analyze_video
from audio.voice_engine import synthesize_narration
from editor.renderer import render_short
from editor.timeline import validate_plan
from services.downloader import download_video


def _set_field(embed: discord.Embed, name: str, value: str) -> None:
    for index, field in enumerate(embed.fields):
        if field.name == name:
            embed.set_field_at(index, name=name, value=value[:1024], inline=False)
            return
    if len(embed.fields) < 25:
        embed.add_field(name=name, value=value[:1024], inline=False)


def register_short_command(tree: app_commands.CommandTree) -> None:
    @tree.command(name="short", description="Buat video Shorts dari URL YouTube.")
    @app_commands.describe(url="URL video YouTube yang akan diproses")
    async def short(interaction: discord.Interaction, url: str) -> None:
        embed = discord.Embed(title="SHORTS MAKER", color=0x5865F2)
        embed.add_field(name="Status", value="Permintaan diterima.", inline=False)
        embed.add_field(name="Sumber video", value=url[:1000], inline=False)
        await interaction.response.send_message(embed=embed)
        original = await interaction.original_response()
        message = original
        fetch_message = getattr(interaction.channel, "fetch_message", None)
        if fetch_message:
            try:
                message = await fetch_message(original.id)
            except discord.HTTPException:
                pass

        async def update(
            status: str,
            stage: str | None = None,
            detail: str | None = None,
            color: int = 0x5865F2,
        ) -> None:
            embed.color = color
            _set_field(embed, "Status", status)
            if stage:
                _set_field(embed, "Tahap", stage)
            if detail:
                _set_field(embed, "Detail", detail)
            await message.edit(embed=embed)

        work_dir = Path(os.getenv("WORK_DIR", "work")) / str(interaction.id)
        work_dir.mkdir(parents=True, exist_ok=True)
        try:
            await update("Mengunduh video...", "1/5 · Download")
            video_path, metadata = await asyncio.to_thread(download_video, url, work_dir)
            await update("Menganalisis isi video...", "2/5 · AI Director", metadata["title"][:250])
            plan, analysis_route = await asyncio.to_thread(
                analyze_video, metadata["webpage_url"], video_path, metadata["duration"]
            )
            clips, narration_text = validate_plan(plan, metadata["duration"])
            timeline_duration = sum(c.output_duration for c in clips)
            await update(
                "Menyusun narasi...", "3/5 · Voice Engine",
                f"Metode analisis: {analysis_route}. Timeline: {timeline_duration:.1f} detik."
            )
            narration_path = work_dir / "narration.wav"
            await asyncio.to_thread(
                synthesize_narration, narration_text, narration_path,
                str(plan.get("style", "natural, clear Indonesian narrator"))
            )
            narration_seconds = await asyncio.to_thread(_probe_seconds, narration_path)
            if not 20 <= narration_seconds <= 180:
                raise ValueError(
                    f"Durasi narasi {narration_seconds:.1f} detik di luar batas 20-180 detik. "
                    "Perlu penyesuaian naskah."
                )
            await update("Merender video vertikal 9:16...", "4/5 · FFmpeg Editor")
            output_path = work_dir / "short.mp4"
            await asyncio.to_thread(
                render_short, video_path, clips, narration_path, output_path, work_dir / "render", plan
            )
            duration_text = await asyncio.to_thread(_probe_duration, output_path)
            file_size = output_path.stat().st_size
            upload_limit = int(getattr(interaction, "filesize_limit", 8 * 1024 * 1024) or 8 * 1024 * 1024)
            title = str(plan.get("title", metadata["title"]))
            size_text = f"{file_size / (1024 * 1024):.1f} MB"

            if file_size > upload_limit:
                embed.title = "SHORTS MAKER · SELESAI"
                embed.color = 0x57F287
                _set_field(embed, "Status", "Video selesai, disimpan untuk GitHub Artifact.")
                _set_field(embed, "Durasi hasil", duration_text)
                _set_field(embed, "Ukuran file", size_text)
                _set_field(embed, "Judul", title[:250])
                _set_field(
                    embed, "Cara mengambil video",
                    "File akan muncul di GitHub Actions → workflow run ini → Artifacts "
                    "setelah sesi bot dihentikan dan workflow menyelesaikan langkah upload."
                )
                await message.edit(embed=embed)
                return

            await update("Mengirim hasil MP4...", "5/5 · Pengiriman")
            try:
                upload = discord.File(str(output_path), filename="short.mp4")
                embed.title = "SHORTS MAKER · SELESAI"
                embed.color = 0x57F287
                _set_field(embed, "Status", "Video berhasil dibuat dan dikirim ke Discord.")
                _set_field(embed, "Durasi hasil", duration_text)
                _set_field(embed, "Ukuran file", size_text)
                _set_field(embed, "Judul", title[:250])
                await message.edit(embed=embed, attachments=[upload])
            except discord.HTTPException:
                embed.title = "SHORTS MAKER · SELESAI"
                embed.color = 0x57F287
                _set_field(embed, "Status", "Video selesai, disimpan untuk GitHub Artifact.")
                _set_field(embed, "Durasi hasil", duration_text)
                _set_field(embed, "Ukuran file", size_text)
                _set_field(embed, "Judul", title[:250])
                _set_field(
                    embed, "Cara mengambil video",
                    "Discord menolak lampiran. File akan tersedia di GitHub Actions → Artifacts "
                    "setelah sesi bot dihentikan dan workflow menyelesaikan langkah upload."
                )
                await message.edit(embed=embed)
        except Exception as exc:
            reason = str(exc).strip() or exc.__class__.__name__
            await update("Proses gagal.", "Error", reason[:900], 0xED4245)


def _probe_seconds(path: Path) -> float:
    import json
    import subprocess
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def _probe_duration(path: Path) -> str:
    seconds = int(_probe_seconds(path))
    minutes, remainder = divmod(seconds, 60)
    return f"{minutes}:{remainder:02d}"
