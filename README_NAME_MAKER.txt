Stylish Name Maker Bot - V3

What changed in V3:
- Keeps the original 39 font converters from the source project.
- Adds generated decorative variants around those converters.
- PREMIUM DESIGN: 156 variants (16 pages at 10 styles/page).
- Aesthetic Art Styles: 107 variants (11 pages at 10 styles/page).
- Live Design: 15 variants (2 pages at 10 styles/page).
- Hindi Live Design: 50 decorative variants suitable for Hindi/English text (5 pages at 10 styles/page).
- Style buttons now preview the current user's name.
- Selected design, Copy Code, Edit Components and pagination are wired together.
- BIO Maker and Bulk Names remain included.
- Bulk picker numbering bug fixed.
- Custom BIO result no longer shows an invalid "Another Bio" button.

Important:
The large style counts are generated variants made from the original font engine plus decorative wrappers. They are not 328 completely different underlying Unicode alphabets.

Environment variables:
BOT_TOKEN=your_bot_token
API_ID=your_api_id
API_HASH=your_api_hash
OWNER_ID=your_telegram_user_id

Run:
python bot.py

Dependencies are kept compatible with the supplied source project.
User state is stored in RAM, so names/bio/bulk state resets after a process restart.
