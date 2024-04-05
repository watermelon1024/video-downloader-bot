"""
Cog module for the download commands.
"""

import asyncio
import os

import discord
import ffmpeg_downloader as ffdl
import yt_dlp

from src.client.i18n import I18n, bool_option, option, slash_command
from src.main import BaseCog, Bot


class DownloadCog(BaseCog):
    """
    The cog class for the download commands.
    """

    async def _run_handler(self, ctx: discord.ApplicationContext, url: str, options: dict):
        await Downloader(ctx, url, options).run()

    @slash_command("download")
    @option("download", "url")
    @option("download", "video_format")
    @option("download", "video_quality")
    @option("download", "audio_format")
    @option("download", "audio_quality")
    @bool_option("download", "audio_only")
    @option("download", "other", required=False)
    async def download(
        self,
        ctx: discord.ApplicationContext,
        url: str,
        video_format: str = None,
        video_quality: str = None,
        audio_format: str = None,
        audio_quality: str = None,
        audio_only: str = "false",
        other: str = None,
    ):
        await ctx.defer()

        options = {"postprocessors": []}
        if video_format or video_quality:
            process = {"key": "FFmpegVideoConvertor"}
            if video_format:
                process["preferedformat"] = video_format
            if video_quality:
                process["custom_params"] = ["-b:v", f"{video_quality.removesuffix('k')}k"]
            options["postprocessors"].append(process)
        if audio_format or audio_quality:
            process = {"key": "FFmpegExtractAudio"}
            if audio_format:
                process["preferredcodec"] = audio_format
            if audio_quality:
                process["preferredquality"] = audio_quality.removesuffix("k")
            options["postprocessors"].append(process)
        if audio_only == "true":
            options = {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": audio_format or "mp3",
                        "preferredquality": (audio_quality or "192").removesuffix("k"),
                    }
                ],
            }

        asyncio.create_task(self._run_handler(ctx, url, options))


class Downloader:
    def __init__(self, ctx: discord.ApplicationContext, url: str, options: dict[str, str] = None):
        self.ctx = ctx
        self.url = url
        self.options = options or {}
        self.options["outtmpl"] = ".cache/videos/%(title)s.%(ext)s"
        self.options["progress_hooks"] = [self._hook]
        self.options["postprocessor_hooks"] = [self._hook]
        self.options["quiet"] = not self.bot.debug_mode
        self.options["no_warnings"] = not self.bot.debug_mode
        self.options["verbose"] = self.bot.debug_mode
        self.options["cachedir"] = ".cache/ytdlp"
        self.options["ffmpeg-location"] = ffdl.ffmpeg_path
        self.file_path = None

    def _hook(self, d):
        if d["status"] == "finished":
            self.file_path = d.get("filename") or d["info_dict"].get("filepath")

    def _download(self):
        with yt_dlp.YoutubeDL(self.options) as ydl:
            ydl.download([self.url])

    async def run(self):
        await self.ctx.respond(I18n.get("slash.download.response.start", self.ctx))
        try:
            self._download()
        except Exception as e:
            error_id = await self.bot.database.new_error_log(e)
            await self.ctx.respond(
                I18n.get("slash.download.response.error", self.ctx, err_id=str(error_id))
            )
            return
        size_in_bytes = os.path.getsize(self.file_path)
        if size_in_bytes > 25000000:  # 25MB
            await self.ctx.respond(
                I18n.get(
                    "slash.download.response.too_large",
                    self.ctx,
                    size=f"{size_in_bytes/1000000:.2f}MB",
                )
            )
        else:
            await self.ctx.edit(
                content=I18n.get("slash.download.response.success", self.ctx),
                file=discord.File(self.file_path),
            )
        os.remove(self.file_path)

    @property
    def bot(self) -> Bot:
        return self.ctx.bot

    @property
    def logger(self):
        return self.bot.logger


def setup(bot: Bot) -> None:
    """
    The setup function of the cog.
    """
    bot.add_cog(DownloadCog(bot))
