# Stylish Name Maker — ফোন থেকে সেটআপ

ভাই, এই project-এ মূল bot code আছে। **`starter_styles.json` আলাদা ফাইল**—ওটা project/GitHub-এ আপলোড করার দরকার নেই; bot চালু হওয়ার পর Telegram-এ পাঠাবে।

## ১) ZIP খুলে GitHub-এ দাও

1. ZIP-টা ফোনের Files/ZArchiver দিয়ে Extract করো।
2. `bot.py`, `requirements.txt`, `.python-version`, `Procfile`, `.gitignore`, `.env.example`, `README.md`, এবং `শুরু_করুন_BN.md` project-এর অংশ।
3. `.env.example`-এ আসল token বা Firebase secret লিখবে না। `starter_styles.json`-ও GitHub-এ দিও না।

## ২) Render-এ চালু করো

একটি Background Worker বানাও।

- Build command: `pip install -r requirements.txt`
- Start command: `python bot.py`
- Python version: `3.11.9`

Environment Variables-এ সেট করো:

- `BOT_TOKEN` — BotFather থেকে bot token
- `ADMIN_IDS` — `8223664417,8819766785`
- `FIREBASE_DATABASE_URL` — Firebase Realtime Database URL
- `FIREBASE_CREDENTIALS_JSON` — Firebase service-account JSON ফাইলের সম্পূর্ণ content একটিমাত্র environment variable-এ

**Service-account JSON বা bot token কখনো GitHub-এ আপলোড করবে না।**

## ৩) Firebase কেন লাগবে?

Firebase সেট না থাকলেও local test mode-এ bot শুরু হতে পারে, কিন্তু Render restart/redeploy হলে local data মুছে যেতে পারে। Style/Category/UI Text স্থায়ী রাখতে Firebase Realtime Database configure করো। Bot নিজের data-টা `/stylish_name_maker` path-এ রাখবে।

## ৪) Bot-এ Style Pack যোগ করো

1. Deploy সফল হলে Telegram-এ নিজের bot খুলে `/start` পাঠাও।
2. অনুমোদিত Admin account থেকে **🛠 Admin Panel** চাপো।
3. **📥 Import JSON → ➕ Merge** বেছে নাও।
4. আলাদা `starter_styles.json` ফাইলটিকে Telegram-এ **document/file** হিসেবে পাঠাও।
5. Import শেষে bot-এ ৫টি Collection ও ১০০টি starter style থাকবে। কোনো gaming category নেই।

## ৫) পরে Style / UI পরিবর্তন

- **➕ Add Style:** নাম, category, font transform এবং template দিয়ে নতুন Style যোগ করো। Template উদাহরণ: `♡ {name} ♡`
- **🧩 Manage Styles:** Style-এর নাম/template/font/category বদলাও, enable/disable বা delete করো।
- **🗂 Manage Categories:** Category add, rename, enable/disable বা delete করো। Category delete করলে তার Style-গুলোও delete হবে।
- **📝 Edit UI Texts:** Welcome text, মূল button label, help, results heading ও category button format পাল্টাও।
- **📥 Import JSON:** নিজের pack merge/replace করো।
- **📤 Export JSON:** আগে backup নিতে পারো। Replace All করার আগে backup নেওয়া ভালো।

সাধারণ Style, Category ও UI Text পরিবর্তনের জন্য GitHub edit বা Render redeploy লাগবে না। Python code-এর নতুন behavior যোগ করতে হলে code update লাগবে।
