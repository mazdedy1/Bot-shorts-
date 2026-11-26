import logging
import os

import discord
from discord import app_commands
from dotenv import load_dotenv

from bot.short_command import register_short_command

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("discord").setLevel(logging.WARNING)


class ShortsBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        register_short_command(self.tree)
        await self.tree.sync()


def main() -> None:
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN belum diatur.")
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY belum diatur.")
    ShortsBot().run(token, log_handler=None)


if __name__ == "__main__":
    main()
