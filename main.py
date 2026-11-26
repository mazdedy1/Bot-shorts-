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
    required = ("DISCORD_TOKEN", "GEMINI_API_KEY")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError("Secret wajib belum diatur: " + ", ".join(missing))
    ShortsBot().run(os.environ["DISCORD_TOKEN"], log_handler=None)


if __name__ == "__main__":
    main()
