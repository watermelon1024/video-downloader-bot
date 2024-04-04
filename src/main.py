"""
The main module of the bot.
"""

import logging
import tracemalloc
from typing import Optional

import discord
from discord.ext import commands

from src.client.config import Config
from src.client.logging import InterceptHandler, Logging


class Bot(discord.AutoShardedBot):
    """
    The modified discord bot client.
    """

    def __init__(self, log_webhook: Optional[str] = None) -> None:
        self._client_ready = False
        self.config = Config()
        self.logger = Logging(
            retention=self.config["log"]["retention"],
            debug_mode=self.config["bot"]["debug-mode"],
            format=self.config["log"]["format"],
        ).get_logger()
        logging.basicConfig(
            handlers=[InterceptHandler(self.logger)],
            level=0 if self.config["bot"]["debug-mode"] else logging.INFO,
            force=True,
        )
        self.log_webhook = log_webhook

        intents = discord.Intents.default()
        intents.members = True
        super().__init__(owner_ids=self.config["bot"]["owners"], intents=intents)

        for k, v in self.load_extension("src.cogs", recursive=True, store=True).items():
            if v is True:
                self.logger.debug(f"Loaded extension {k}")
            else:
                self.logger.error(f"Failed to load extension {k} with exception: {v}")

    async def on_start(self) -> None:
        """
        The event that is triggered when the bot is started.
        """
        self._uptime = discord.utils.utcnow()  # Store a timezone-aware datetime object
        self.logger.info(
            f"""
-------------------------
Logged in as: {self.user.name}#{self.user.discriminator} ({self.user.id})
Shards Count: {self.shard_count}
Memory Usage: {tracemalloc.get_traced_memory()[0] / 1024 ** 2:.2f} MB
 API Latency: {self.latency * 1000:.2f} ms
Guilds Count: {len(self.guilds)}
-------------------------"""
        )

    async def on_ready(self) -> None:
        """
        The event that is triggered when the bot is ready.
        """
        if self._client_ready:
            return
        await self.on_start()
        self._client_ready = True

    async def close(self) -> None:
        return await super().close()

    @property
    def uptime(self) -> Optional[int]:
        """
        The uptime of the bot in seconds.

        :return: The uptime of the bot in seconds or None if the bot is not ready.
        :rtype: Optional[int]
        """
        if not hasattr(self, "_uptime"):
            return None
        return (discord.utils.utcnow() - self._uptime).total_seconds()


class BaseCog(commands.Cog):
    """
    The base cog class.
    """

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.logger = bot.logger
