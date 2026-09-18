Stylish Name Maker Bot - V5

Render-ready dependency update based on V4.

Features:
- Stylish Name Maker
- Premium / Aesthetic / Live / Bangla Live categories
- Pagination and copy-ready generated names
- BIO Maker
- Bulk Name Maker
- Original font engine retained

Environment variables on Render:
BOT_TOKEN=your_bot_token
API_ID=your_api_id
API_HASH=your_api_hash
OWNER_ID=your_telegram_user_id

Python:
3.11.9

Run:
python bot.py

Important:
- Do not add async-lru manually.
- Pyrogram 2.0.106 is used instead of the old Pyrogram 1.2.9 dependency chain.
- User state is stored in RAM and resets when the process restarts.
