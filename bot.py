import logging

from pyrogram import Client
from config import Config
from commands import register_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


app = Client(
    "StylishNameMakerBot",
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    workers=100,
)

register_handlers(app)


if __name__ == "__main__":
    app.run()
