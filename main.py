import http.server
import os
import socketserver
import threading
import time
import math
import telebot
from telebot import types

# --- RENDER KEEP ALIVE WEBSERVER ---
class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Stylish Name Maker Bot is Online!")

    def log_message(self, format, *args):
        return

def run_web_server():
    port = int(os.getenv("PORT", 8080))
    try:
        with socketserver.TCPServer(("", port), HealthCheckHandler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        print(f"Web server error: {e}")

threading.Thread(target=run_web_server, daemon=True).start()

# --- TELEGRAM BOT & CHANNEL CONFIGURATION ---
BOT_TOKEN = os.getenv("BOT_TOKEN") 
REQUIRED_CHANNEL = os.getenv("CHANNEL_USERNAME", "@JisanGaming") # আপনার চ্যানেলের ইউজারনেম

if not BOT_TOKEN:
    raise ValueError("Error: BOT_TOKEN Environment Variable is missing!")

bot = telebot.TeleBot(BOT_TOKEN)

# User State Database (In-Memory)
user_states = {}
user_names = {}

# --- AESTHETIC GREEK FONT CONVERTER ---
# এই ফন্ট ইঞ্জিনটি আপনার স্ক্রিনশটের মতো "Jisan" কে "Jιδαη" বানাবে
GREEK_MAP = {
    'a': 'α', 'b': 'ϐ', 'c': 'c', 'd': '∂', 'e': 'є', 'f': 'ɟ', 
    'g': 'g', 'h': 'н', 'i': 'ι', 'j': 'j', 'k': 'κ', 'l': 'ℓ', 
    'm': 'м', 'n': 'η', 'o': 'σ', 'p': 'ρ', 'q': 'q', 'r': 'я', 
    's': 'δ', 't': 'т', 'u': 'υ', 'v': 'ν', 'w': 'ω', 'x': 'x', 
    'y': 'у', 'z': 'z',
    'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D', 'E': 'E', 'F': 'F', 
    'G': 'G', 'H': 'H', 'I': 'I', 'J': 'J', 'K': 'K', 'L': 'L', 
    'M': 'M', 'N': 'N', 'O': 'O', 'P': 'P', 'Q': 'Q', 'R': 'R', 
    'S': 'S', 'T': 'T', 'U': 'U', 'V': 'V', 'W': 'W', 'X': 'X', 
    'Y': 'Y', 'Z': 'Z'
}

def to_greek_font(text):
    return "".join(GREEK_MAP.get(char, char) for char in text)

# --- EXACT 30 TEMPLATES FROM YOUR SCREENSHOTS ---
AESTHETIC_STYLES = [
    "⑅🤍{name}─f🫶🏻",          # 1
    '"{name}🎀"',               # 2
    "⑅{name}🦋 ⃟∘",             # 3
    "૮ ⚞ {name} ⚟ ꨄ︎",         # 4
    "─ ☾🌹{name}🪷 ⃟∘",         # 5
    '──"{name}🌷',              # 6
    "─ {name}♡ ─ 🫀🔪 ═",        # 7
    "⑅* ༄ {name} ~ 🦋 ╰╮",     # 8
    "─ {name} 🎣 ⃟∘",           # 9
    "🌷{name} 🫶🏻 🫧 ‧₊˚.",      # 10
    "── {name}🤍 ── ═",         # 11
    "◀ 🦋 ⃟∘ {name} 🤍 ✖",      # 12
    "⚚ ⑅ ⚚ {name} ⚚ ⑅ ⚚",       # 13
    "🌿 {name} 🌿 ── ⚲ ⚲",      # 14
    "─ ⎩ {name} ⎭ ─ 🎀 ☾",      # 15
    "─ {name} 🦋 🌿",           # 16
    "─ {name} ─ 💖",            # 17
    "⑅═ {name} ═ 💔",           # 18
    "─ {name} ─ 🤍",            # 19
    "✨ {name} ✨ 🦋",           # 20
    "─ ✝ {name} ✝ ─ ﮩ٨ـ 🖤",    # 21
    "💎 ⎩ {name} ⎭ 🎀 ☾",       # 22
    "🌙 {name} 🌙 👼",          # 23
    "🪷 ∘ {name} 🪷",           # 24
    "🦅 {name} 👑 🦅 ─ ✨",      # 25 (Eagle theme for brand)
    "⚡ {name} ⚡ 🎶",           # 26
    "─ ⎩ 🌹 {name} 🌹 ⎭ ─ 🔑",  # 27
    "☠ {name} ☠ 💔",            # 28
    "⑅═ ∞ {name} ∞ ─ 💖",       # 29
    "❄️ {name} ❄️ 〰"             # 30
]

# Premium & Live Designs (Adding some samples so they work flawlessly)
PREMIUM_STYLES = [f"『VIP』•{{name}}", f"༒•{{name}}•༒", f"⪻{{name}}⪼", f"★彡[{{name}}]彡★", f"⚡{{name}}⚡", f"👑{{name}}👑"] * 5
LIVE_STYLES = [f"꧁ঔ𝟷𝟾𝟺+{{name}}†ঔ꧂", f"⚔️ {{name}} ⚔️", f"🎯 {{name}} 🎯", f"亗 {{name}} 亗", f"🩸 {{name}} 🩸"] * 6

CATEGORIES = {
    "premium": {"name": "👑 PREMIUM DESIGN", "data": PREMIUM_STYLES},
    "aesthetic": {"name": "✨ Aesthetic Art Styles", "data": AESTHETIC_STYLES},
    "live": {"name": "🎬 Live Design", "data": LIVE_STYLES}
}

ITEMS_PER_PAGE = 10

# Helper: Channel Membership Check
def is_user_joined(user_id):
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return True 

def send_force_join_msg(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    channel_link = f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}"
    markup.add(
        types.InlineKeyboardButton(f"🔗 Join: {REQUIRED_CHANNEL}", url=channel_link),
        types.InlineKeyboardButton("✅ Joined – Verify", callback_data="check_join")
    )
    msg_text = "📢 **TO USE THIS BOT, YOU MUST JOIN OUR CHANNEL FIRST!**\n\nবটটি ব্যবহার করতে আমাদের চ্যানেলে জয়েন করুন। জয়েন করার পর নিচে **Verify** বাটনে চাপ দিন।"
    bot.send_message(chat_id, msg_text, parse_mode="Markdown", reply_markup=markup)

def send_main_menu(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✏️ Make My Name", callback_data="make_name"),
        types.InlineKeyboardButton("📝 BIO", callback_data="bio_options"),
        types.InlineKeyboardButton("🚀 Bulk Names", callback_data="bulk_names"),
        types.InlineKeyboardButton("❓ Help", callback_data="help_msg")
    )
    menu_text = "✨ **Welcome to Stylish Name Maker Bot!** ✨\n\n👇 **নিচের বাটন থেকে অপশন সিলেক্ট করুন:**"
    bot.send_message(chat_id, menu_text, parse_mode="Markdown", reply_markup=markup)

def generate_pagination_markup(category_key, current_page):
    markup = types.InlineKeyboardMarkup(row_width=1)
    styles = CATEGORIES[category_key]["data"]
    total_pages = math.ceil(len(styles) / ITEMS_PER_PAGE)
    
    start_idx = (current_page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    page_styles = styles[start_idx:end_idx]

    # Generate Name Buttons (1-10, 11-20, etc.)
    for idx, template in enumerate(page_styles, start=start_idx + 1):
        # We don't render the name here, we send format instruction so user can copy
        markup.add(types.InlineKeyboardButton(text=f"{idx}. {template.format(name='Name')}", callback_data="copy_hint"))

    # Pagination Controls [Previous] [Page X/Y] [Next]
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(types.InlineKeyboardButton("⬅️ Previous", callback_data=f"page_{category_key}_{current_page - 1}"))
    
    nav_buttons.append(types.InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="ignore"))
    
    if current_page < total_pages:
        nav_buttons.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"page_{category_key}_{current_page + 1}"))
    
    markup.row(*nav_buttons)
    markup.row(types.InlineKeyboardButton("⬅️ Back", callback_data="show_categories"), 
               types.InlineKeyboardButton("✏️ New Name", callback_data="make_name"),
               types.InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu"))
    
    return markup

# --- COMMANDS ---
@bot.message_handler(commands=["start"])
def handle_start(message):
    if not is_user_joined(message.from_user.id):
        send_force_join_msg(message.chat.id)
    else:
        send_main_menu(message.chat.id)

# --- TEXT HANDLER ---
@bot.message_handler(func=lambda msg: True)
def handle_text(message):
    user_id = message.from_user.id
    if not is_user_joined(user_id):
        send_force_join_msg(message.chat.id)
        return

    if user_states.get(user_id) == "waiting_for_name":
        raw_name = message.text.strip()
        user_names[user_id] = raw_name
        user_states[user_id] = None 
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton(f"{CATEGORIES['premium']['name']} (30 Styles)", callback_data="page_premium_1"),
            types.InlineKeyboardButton(f"{CATEGORIES['aesthetic']['name']} (30 Styles)", callback_data="page_aesthetic_1"),
            types.InlineKeyboardButton(f"{CATEGORIES['live']['name']} (30 Styles)", callback_data="page_live_1")
        )
        markup.row(types.InlineKeyboardButton("✏️ New Name", callback_data="make_name"), types.InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu"))
        
        bot.send_message(message.chat.id, f"✅ **Name:** `{raw_name}`\n\n👇 **নিচের ৩টি ক্যাটাগরি থেকে সিলেক্ট করুন:**", parse_mode="Markdown", reply_markup=markup)
    else:
        send_main_menu(message.chat.id)

# --- CALLBACK HANDLERS ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if call.data == "check_join":
        if is_user_joined(user_id):
            bot.answer_callback_query(call.id, "✅ Verification Successful!")
            bot.delete_message(chat_id, call.message.message_id)
            send_main_menu(chat_id)
        else:
            bot.answer_callback_query(call.id, "❌ আপনি এখনও চ্যানেলে জয়েন করেননি!", show_alert=True)

    elif call.data == "main_menu":
        bot.delete_message(chat_id, call.message.message_id)
        send_main_menu(chat_id)

    elif call.data == "make_name":
        user_states[user_id] = "waiting_for_name"
        bot.send_message(chat_id, "✍️ **যেই নামটি স্টাইলিশ করতে চান সেটি লিখে পাঠান:**", parse_mode="Markdown")

    elif call.data == "show_categories":
        raw_name = user_names.get(user_id, "Jisan")
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton(f"{CATEGORIES['premium']['name']} (30 Styles)", callback_data="page_premium_1"),
            types.InlineKeyboardButton(f"{CATEGORIES['aesthetic']['name']} (30 Styles)", callback_data="page_aesthetic_1"),
            types.InlineKeyboardButton(f"{CATEGORIES['live']['name']} (30 Styles)", callback_data="page_live_1")
        )
        markup.row(types.InlineKeyboardButton("✏️ New Name", callback_data="make_name"), types.InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu"))
        bot.edit_message_text(f"✅ **Name:** `{raw_name}`\n\n👇 **নিচের ৩টি ক্যাটাগরি থেকে সিলেক্ট করুন:**", chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif call.data.startswith("page_"):
        _, category, page_str = call.data.split("_")
        current_page = int(page_str)
        
        raw_name = user_names.get(user_id, "Jisan")
        
        # গ্রীক ফন্টে কনভার্ট করা (শুধু Aesthetic এর জন্য)
        if category == "aesthetic":
            styled_name = to_greek_font(raw_name)
        else:
            styled_name = raw_name

        markup = types.InlineKeyboardMarkup(row_width=1)
        styles = CATEGORIES[category]["data"]
        total_pages = math.ceil(len(styles) / ITEMS_PER_PAGE)
        start_idx = (current_page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        page_styles = styles[start_idx:end_idx]

        # জেনারেটেড নাম বাটনে দেখানো
        for idx, template in enumerate(page_styles, start=start_idx + 1):
            final_text = f"{idx}. " + template.format(name=styled_name)
            # বাটনে চাপ দিলে অটো কপি হওয়ার জন্য Callback
            markup.add(types.InlineKeyboardButton(text=final_text, callback_data="ignore"))

        nav_buttons = []
        if current_page > 1:
            nav_buttons.append(types.InlineKeyboardButton("⬅️ Previous", callback_data=f"page_{category}_{current_page - 1}"))
        
        nav_buttons.append(types.InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="ignore"))
        
        if current_page < total_pages:
            nav_buttons.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"page_{category}_{current_page + 1}"))
        
        markup.row(*nav_buttons)
        markup.row(types.InlineKeyboardButton("⬅️ Back", callback_data="show_categories"), 
                   types.InlineKeyboardButton("✏️ New Name", callback_data="make_name"),
                   types.InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu"))
        
        msg = "👇 **কপি করতে মেসেজটি ট্যাপ করে ধরে রাখুন:**\n*(Telegram Update এর কারণে ডাইরেক্ট বাটনে কপি সাপোর্ট করে না, বাটনের নামগুলো মেসেজে দিয়ে দিচ্ছি)*\n\n"
        for idx, template in enumerate(page_styles, start=start_idx + 1):
             msg += f"`{template.format(name=styled_name)}`\n"

        bot.edit_message_text(msg, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif call.data == "ignore":
        bot.answer_callback_query(call.id, "Tip: কপি করতে মেসেজের টেক্সটের ওপর চাপ দিন!")

# --- BOT STARTUP ENGINE ---
print("Stylish Name Maker Bot Started...")
while True:
    try:
        bot.infinity_polling(skip_pending=True, timeout=20)
    except Exception as e:
        print(f"Polling Exception: {e}")
        time.sleep(5)
