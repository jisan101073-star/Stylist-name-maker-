import os
import telebot
from telebot import types
import threading
import http.server
import socketserver

# ============================================================================
# ENVIRONMENT VARIABLES (CRITICAL: Set in Render Dashboard)
# ============================================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME")
PORT = int(os.getenv("PORT", 8080))

if not BOT_TOKEN or not CHANNEL_USERNAME:
    raise ValueError(
        "❌ CRITICAL ERROR: BOT_TOKEN and CHANNEL_USERNAME must be set in Render Environment Variables."
    )

bot = telebot.TeleBot(BOT_TOKEN)

# ============================================================================
# FONT ENGINE: Unicode Character Mappings
# ============================================================================

SMALL_CAPS_MAP = {
    'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ',
    'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 'ꜱ', 't': 'ᴛ',
    'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
    'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D', 'E': 'E', 'F': 'F', 'G': 'G', 'H': 'H', 'I': 'I', 'J': 'J',
    'K': 'K', 'L': 'L', 'M': 'M', 'N': 'N', 'O': 'O', 'P': 'P', 'Q': 'Q', 'R': 'R', 'S': 'S', 'T': 'T',
    'U': 'U', 'V': 'V', 'W': 'W', 'X': 'X', 'Y': 'Y', 'Z': 'Z',
}

AESTHETIC_GREEK_MAP = {
    'a': 'α', 'b': 'ϐ', 'c': 'ϲ', 'd': '∂', 'e': 'є', 'f': 'ϝ', 'g': 'ց', 'h': 'һ', 'i': 'ι', 'j': 'ј',
    'k': 'κ', 'l': 'ℓ', 'm': 'м', 'n': 'η', 'o': 'σ', 'p': 'ρ', 'q': 'ϙ', 'r': 'ṛ', 's': 'δ', 't': 'τ',
    'u': 'υ', 'v': 'ν', 'w': 'ω', 'x': 'χ', 'y': 'ψ', 'z': 'ζ',
    'A': 'Α', 'B': 'Β', 'C': 'Ϲ', 'D': 'Δ', 'E': 'Ε', 'F': 'Ϝ', 'G': 'Γ', 'H': 'Η', 'I': 'Ι', 'J': 'Ϳ',
    'K': 'Κ', 'L': 'Λ', 'M': 'Μ', 'N': 'Ν', 'O': 'Ο', 'P': 'Ρ', 'Q': 'Ϙ', 'R': 'Ρ', 'S': 'Σ', 'T': 'Τ',
    'U': 'Υ', 'V': 'Ν', 'W': 'Ω', 'X': 'Χ', 'Y': 'Ψ', 'Z': 'Ζ',
}

GOTHIC_MAP = {
    'a': '𝔞', 'b': '𝔟', 'c': '𝔠', 'd': '𝔡', 'e': '𝔢', 'f': '𝔣', 'g': '𝔤', 'h': '𝔥', 'i': '𝔦', 'j': '𝔧',
    'k': '𝔨', 'l': '𝔩', 'm': '𝔪', 'n': '𝔫', 'o': '𝔬', 'p': '𝔭', 'q': '𝔮', 'r': '𝔯', 's': '𝔰', 't': '𝔱',
    'u': '𝔲', 'v': '𝔳', 'w': '𝔴', 'x': '𝔵', 'y': '𝔶', 'z': '𝔷',
    'A': '𝔄', 'B': '𝔅', 'C': '𝔆', 'D': '𝔇', 'E': '𝔈', 'F': '𝔉', 'G': '𝔊', 'H': '𝔉', 'I': '𝔍', 'J': '𝔎',
    'K': '𝔎', 'L': '𝔏', 'M': '𝔐', 'N': '𝔑', 'O': '𝔒', 'P': '𝔓', 'Q': '𝔔', 'R': '𝔖', 'S': '𝔖', 'T': '𝔗',
    'U': '𝔘', 'V': '𝔙', 'W': '𝔚', 'X': '𝔛', 'Y': '𝔜', 'Z': '𝔃',
}

def convert_text(text, font_map):
    return ''.join(font_map.get(char, char) for char in text)

# ============================================================================
# TRANSLATIONS
# ============================================================================
TRANSLATIONS = {
    'en': {
        'greeting': '👋 Welcome to Stylish Name Maker! Choose your language:',
        'language': 'Language Selected: English ✅',
        'channel_join': '⚠️ *You must join our channel first!*\n\nPlease click the button below to join our channel, then click "Verify" to continue.',
        'verify': '✅ Thanks for joining! You now have full access.',
        'welcome': '✨ *Welcome to Your Name Studio!* ✨\n\nChoose what you\'d like to do:',
        'make_name': '✍️ Enter your name:',
        'choose_category': '🎨 Choose a design style category:',
        'premium_design': '👑 Premium Design',
        'aesthetic_art': '✨ Aesthetic Art Styles',
        'live_design': '🎬 Live Design',
        'help': '❓ Help',
        'bio': '📝 BIO',
        'bulk': '🚀 Bulk Names',
        'coming_soon': '🚧 Coming Soon! This feature will be available very soon.',
        'selected_design': '✨ Your Selected Design:',
        'copy': '📋 Copy Code',
        'copied': '✅ Text copied to clipboard!',
        'back': '⬅️ Back',
        'new_name': '✏️ New Name',
        'main_menu': '🏠 Main Menu',
        'page': 'Page',
        'previous': '⬅️ Previous',
        'next': 'Next ➡️',
        'back_category': '⬅️ Back to Categories',
        'join_channel': '🔗 Join Our Channel',
        'verify_join': '✅ Joined - Verify',
    },
    'bn': {
        'greeting': '👋 স্টাইলিশ নাম মেকারে স্বাগতম! আপনার ভাষা বেছে নিন:',
        'language': 'নির্বাচিত ভাষা: বাংলা ✅',
        'channel_join': '⚠️ *আপনাকে আগে আমাদের চ্যানেলে যোগ দিতে হবে!*\n\nনীচের বাটনে ক্লিক করে আমাদের চ্যানেলে যোগ দিন, তারপর "Verify" বাটনে ক্লিক করুন।',
        'verify': '✅ জয়েন করার জন্য ধন্যবাদ! আপনি এখন বটটি ব্যবহার করতে পারবেন।',
        'welcome': '✨ *আপনার নেম স্টুডিওতে স্বাগতম!* ✨\n\nআপনি কী করতে চান তা বেছে নিন:',
        'make_name': '✍️ আপনার নাম লিখুন:',
        'choose_category': '🎨 একটি ডিজাইন ক্যাটাগরি বেছে নিন:',
        'premium_design': '👑 Premium Design',
        'aesthetic_art': '✨ Aesthetic Art Styles',
        'live_design': '🎬 Live Design',
        'help': '❓ সাহায্য',
        'bio': '📝 BIO',
        'bulk': '🚀 Bulk Names',
        'coming_soon': '🚧 শীঘ্রই আসছে! এই ফিচারটি খুব তাড়াতাড়ি যোগ করা হবে।',
        'selected_design': '✨ আপনার নির্বাচিত ডিজাইন:',
        'copy': '📋 Copy Code',
        'copied': '✅ টেক্সট কপি করা হয়েছে!',
        'back': '⬅️ ফিরে যান',
        'new_name': '✏️ নতুন নাম',
        'main_menu': '🏠 প্রধান মেনু',
        'page': 'পৃষ্ঠা',
        'previous': '⬅️ আগের পেইজ',
        'next': 'পরের পেইজ ➡️',
        'back_category': '⬅️ ক্যাটাগরিতে ফিরে যান',
        'join_channel': '🔗 আমাদের চ্যানেলে যোগ দিন',
        'verify_join': '✅ জয়েন করেছি - Verify',
    }
}

user_data = {}

def get_user_data(user_id):
    if user_id not in user_data:
        user_data[user_id] = {'language': 'en', 'joined_channel': False, 'current_name': '', 'current_category': None, 'current_page': 0}
    return user_data[user_id]

def t(user_id, key):
    lang = get_user_data(user_id).get('language', 'en')
    return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)

# ============================================================================
# 90 STYLED TEMPLATES (30 per category)
# ============================================================================
STYLE_TEMPLATES = {
    'premium': [
        '═ {name} ═', '─ {name} ─', '▪ {name} ▪', '◆ {name} ◆', '★ {name} ★', '✦ {name} ✦', '» {name} «', '› {name} ‹', '║ {name} ║', '▬ {name} ▬',
        '❖ {name} ❖', '⟡ {name} ⟡', '◇ {name} ◇', '✧ {name} ✧', '⚜ {name} ⚜', '✪ {name} ✪', '◈ {name} ◈', '⬩ {name} ⬩', '▲ {name} ▲', '▼ {name} ▼',
        '◀ {name} ▶', '❖ {name} ❖', '⟪ {name} ⟫', '∞ {name} ∞', '⊱ {name} ⊰', '❈ {name} ❈', '◆◆ {name} ◆◆', '▬▬ {name} ▬▬', '✦✦ {name} ✦✦', '۞ {name} ۞',
    ],
    'aesthetic': [
        '─ {name} ♡ ─ 🫀🔪 ═', '⑅🤍{name}─🫶🏻', '• {name} •', '◦ {name} ◦', '⚬ {name} ⚬', '۰ {name} ۰', '⊙ {name} ⊙', '❁ {name} ❁', '❀ {name} ❀', '✿ {name} ✿',
        '❃ {name} ❃', '❉ {name} ❉', '☆ {name} ☆', '✡ {name} ✡', '⭐ {name} ⭐', '✤ {name} ✤', '✥ {name} ✥', '✼ {name} ✼', '✾ {name} ✾', '❋ {name} ❋',
        '❊ {name} ❊', '⟐ {name} ⟐', '❂ {name} ❂', '❄ {name} ❄', '❅ {name} ❅', '❆ {name} ❆', '❇ {name} ❇', '❈ {name} ❈', '✧ {name} ✧', '⟡ {name} ⟡',
    ],
    'live': [
        '《 {name} 》', '〈 {name} 〉', '【 {name} 】', '『 {name} 』', '「 {name} 」', '＜ {name} ＞', '＿ {name} ＿', '※ {name} ※', '§ {name} §', '¤ {name} ¤',
        '◎ {name} ◎', '◉ {name} ◉', '⌬ {name} ⌬', '⌭ {name} ⌭', '⌮ {name} ⌮', '⌯ {name} ⌯', '⌰ {name} ⌰', '⌱ {name} ⌱', '⌲ {name} ⌲', '⌳ {name} ⌳',
        '⌴ {name} ⌴', '⌵ {name} ⌵', '⌶ {name} ⌶', '⌷ {name} ⌷', '⌸ {name} ⌸', '⌹ {name} ⌹', '⌺ {name} ⌺', '⌻ {name} ⌻', '⌼ {name} ⌼', '⌾ {name} ⌾',
    ]
}

def get_font_map(category):
    if category == 'premium': return SMALL_CAPS_MAP
    elif category == 'aesthetic': return AESTHETIC_GREEK_MAP
    elif category == 'live': return GOTHIC_MAP
    return {}

def is_user_in_channel(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

# ============================================================================
# COMMAND HANDLERS
# ============================================================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("🇧🇩 Bengali", callback_data='lang_bn'),
        types.InlineKeyboardButton("🇬🇧 English", callback_data='lang_en')
    )
    bot.send_message(user_id, "👋 Welcome to Stylish Name Maker! Choose your language / আপনার ভাষা বেছে নিন:", reply_markup=keyboard)

# ============================================================================
# UI FUNCTIONS
# ============================================================================
def check_channel_membership(user_id):
    if is_user_in_channel(user_id):
        get_user_data(user_id)['joined_channel'] = True
        show_main_menu(user_id)
    else:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            types.InlineKeyboardButton(t(user_id, 'join_channel'), url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"),
            types.InlineKeyboardButton(t(user_id, 'verify_join'), callback_data='join_channel')
        )
        bot.send_message(user_id, t(user_id, 'channel_join'), parse_mode='Markdown', reply_markup=keyboard)

def show_main_menu(user_id):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton('✏️ Make My Name', callback_data='make_name'),
        types.InlineKeyboardButton('📝 BIO', callback_data='bio'),
        types.InlineKeyboardButton('🚀 Bulk Names', callback_data='bulk'),
        types.InlineKeyboardButton('❓ Help', callback_data='help')
    )
    bot.send_message(user_id, t(user_id, 'welcome'), parse_mode='Markdown', reply_markup=keyboard)

def show_category_selection(user_id):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton(t(user_id, 'premium_design'), callback_data='category_premium'),
        types.InlineKeyboardButton(t(user_id, 'aesthetic_art'), callback_data='category_aesthetic'),
        types.InlineKeyboardButton(t(user_id, 'live_design'), callback_data='category_live'),
        types.InlineKeyboardButton(t(user_id, 'main_menu'), callback_data='main_menu')
    )
    bot.send_message(user_id, t(user_id, 'choose_category'), parse_mode='Markdown', reply_markup=keyboard)

def process_name_input(message):
    user_id = message.from_user.id
    if not message.text:
        return
    get_user_data(user_id)['current_name'] = message.text.strip()
    show_category_selection(user_id)

def show_styles_page(user_id, category, page, message_id=None):
    data = get_user_data(user_id)
    name = data['current_name']
    font_map = get_font_map(category)
    templates = STYLE_TEMPLATES[category]
    
    start = page * 10
    end = start + 10
    page_templates = templates[start:end]
    total_pages = (len(templates) + 9) // 10
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    for idx, template in enumerate(page_templates, start=start):
        styled_name = template.format(name=convert_text(name, font_map))
        btn_text = f"{idx + 1}. {styled_name}"
        keyboard.add(types.InlineKeyboardButton(btn_text, callback_data=f"style_{category}_{idx}"))
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton(t(user_id, 'previous'), callback_data=f"page_{category}_{page-1}"))
    nav_buttons.append(types.InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="ignore"))
    if page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton(t(user_id, 'next'), callback_data=f"page_{category}_{page+1}"))
    
    if nav_buttons:
        keyboard.row(*nav_buttons)
        
    keyboard.row(
        types.InlineKeyboardButton(t(user_id, 'back_category'), callback_data='back_category'),
        types.InlineKeyboardButton(t(user_id, 'new_name'), callback_data='make_name')
    )
    keyboard.add(types.InlineKeyboardButton(t(user_id, 'main_menu'), callback_data='main_menu'))
    
    text = t(user_id, 'choose_category')
    if message_id:
        bot.edit_message_text(text, user_id, message_id, reply_markup=keyboard, parse_mode='Markdown')
    else:
        bot.send_message(user_id, text, reply_markup=keyboard, parse_mode='Markdown')

def show_selected_design(user_id, styled_name, category, page, message_id):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton(t(user_id, 'copy'), callback_data=f"copy_{styled_name}"),
        types.InlineKeyboardButton(t(user_id, 'back'), callback_data=f"page_{category}_{page}"),
        types.InlineKeyboardButton(t(user_id, 'main_menu'), callback_data='main_menu')
    )
    
    text = f"{t(user_id, 'selected_design')}\n\n`{styled_name}`"
    bot.edit_message_text(text, user_id, message_id, reply_markup=keyboard, parse_mode='Markdown')

# ============================================================================
# CALLBACK HANDLERS
# ============================================================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    data = call.data
    
    if data.startswith('lang_'):
        get_user_data(user_id)['language'] = data.split('_')[1]
        bot.answer_callback_query(call.id)
        bot.delete_message(user_id, call.message.message_id)
        check_channel_membership(user_id)
        
    elif data == 'join_channel':
        if is_user_in_channel(user_id):
            get_user_data(user_id)['joined_channel'] = True
            bot.answer_callback_query(call.id, t(user_id, 'verify'), show_alert=True)
            bot.delete_message(user_id, call.message.message_id)
            show_main_menu(user_id)
        else:
            bot.answer_callback_query(call.id, "❌ Please join the channel first!", show_alert=True)
            
    elif data == 'make_name':
        bot.answer_callback_query(call.id)
        bot.delete_message(user_id, call.message.message_id)
        msg = bot.send_message(user_id, t(user_id, 'make_name'))
        bot.register_next_step_handler(msg, process_name_input)
        
    elif data in ['bio', 'bulk']:
        bot.answer_callback_query(call.id, t(user_id, 'coming_soon'), show_alert=True)
        
    elif data == 'help':
        bot.answer_callback_query(call.id)
        bot.send_message(user_id, "🎨 *Stylish Name Maker Help*\n\n1️⃣ *Make My Name* - Create stylish versions of your name\n2️⃣ *Choose Category* - Select from 3 design styles\n3️⃣ *Browse Styles* - 30 unique templates per category\n4️⃣ *Copy Design* - Tap to copy your favorite style", parse_mode='Markdown')
        
    elif data.startswith('category_'):
        category = data.split('_')[1]
        get_user_data(user_id)['current_category'] = category
        get_user_data(user_id)['current_page'] = 0
        bot.answer_callback_query(call.id)
        show_styles_page(user_id, category, 0, call.message.message_id)
        
    elif data.startswith('style_'):
        _, category, style_idx = data.split('_')
        style_idx = int(style_idx)
        user_name = get_user_data(user_id)['current_name']
        page = get_user_data(user_id)['current_page']
        
        font_map = get_font_map(category)
        template = STYLE_TEMPLATES[category][style_idx]
        styled_name = template.format(name=convert_text(user_name, font_map))
        
        bot.answer_callback_query(call.id)
        show_selected_design(user_id, styled_name, category, page, call.message.message_id)
        
    elif data.startswith('page_'):
        _, category, page = data.split('_')
        get_user_data(user_id)['current_page'] = int(page)
        bot.answer_callback_query(call.id)
        show_styles_page(user_id, category, int(page), call.message.message_id)
        
    elif data == 'back_category':
        bot.answer_callback_query(call.id)
        bot.delete_message(user_id, call.message.message_id)
        show_category_selection(user_id)
        
    elif data == 'main_menu':
        bot.answer_callback_query(call.id)
        bot.delete_message(user_id, call.message.message_id)
        show_main_menu(user_id)
        
    elif data.startswith('copy_'):
        bot.answer_callback_query(call.id, t(user_id, 'copied'), show_alert=True)
        
    elif data == 'ignore':
        bot.answer_callback_query(call.id)

# ============================================================================
# RENDER KEEP-ALIVE SERVER
# ============================================================================
class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running smoothly!")
    def log_message(self, format, *args):
        pass

def run_server():
    with socketserver.TCPServer(("", PORT), HealthCheckHandler) as httpd:
        print(f"Web server active on port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    print("Bot is polling...")
    bot.infinity_polling()
