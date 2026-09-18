import logging

from pyrogram import Client
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

if __name__ == "__main__":
    plugins = {"root": "plugins"}

    app = Client(
        "StylishNameMakerBot",
        bot_token=Config.BOT_TOKEN,
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        plugins=plugins,
        workers=100,
    )

    app.run()
