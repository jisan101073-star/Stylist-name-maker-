from config import Config
from fonts import Fonts
from pyrogram import filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


# =========================================================
# Stylish Name Maker Bot — V3
# =========================================================
# Name style variants are generated from the original 39 font
# converters plus decorative wrappers. This gives the bot a much
# larger library while keeping the original font engine intact.
USER_STATE = {}
USER_NAME = {}
USER_BIO = {}
USER_BULK = {}


# ------------------------- MENUS --------------------------
def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✏️ Make My Name", callback_data="menu_name"),
            InlineKeyboardButton("📝 BIO", callback_data="menu_bio"),
        ],
        [
            InlineKeyboardButton("🚀 Bulk Names", callback_data="menu_bulk"),
            InlineKeyboardButton("❓ Help", callback_data="menu_help"),
        ],
    ])


def category_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👑 PREMIUM DESIGN", callback_data="cat_premium")],
        [InlineKeyboardButton("✨ Aesthetic Art Styles", callback_data="cat_aesthetic")],
        [InlineKeyboardButton("🎬 Live Design", callback_data="cat_live")],
        [InlineKeyboardButton("🇧🇩 Bangla Live Design", callback_data="cat_bangla")],
        [
            InlineKeyboardButton("✏️ New Name", callback_data="menu_name"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="home"),
        ],
    ])


# ------------------------- FONT MAP -----------------------
# The reference bot uses clearly different Unicode font families.  V4 keeps the
# original 39 font converters, but removes the heavy prefix/suffix wrappers from
# the name buttons.  Extra variants use clean typography treatments only.
STYLE_MAP = {
    "typewriter": ("𝚃𝚢𝚙𝚎𝚠𝚛𝚒𝚝𝚎𝚛", Fonts.typewriter),
    "outline": ("𝕆𝕦𝕥𝕝𝕚𝕟𝕖", Fonts.outline),
    "serief": ("𝐒𝐞𝐫𝐢𝐟", Fonts.serief),
    "bold_cool": ("𝑺𝒄𝒓𝒊𝒑𝒕 𝐁𝐨𝐥𝐝", Fonts.bold_cool),
    "cool": ("𝑆𝑒𝑟𝑖𝑓 𝐈𝐭𝐚𝐥𝕚𝕔", Fonts.cool),
    "smallcap": ("Sᴍᴀʟʟ Cᴀᴘs", Fonts.smallcap),
    "script": ("𝒮𝒸𝓇𝒾𝓅𝓉", Fonts.script),
    "bold_script": ("𝓑𝓸𝓵𝓭 𝓢𝓬𝓻𝓲𝓹𝓽", Fonts.bold_script),
    "tiny": ("ᵀⁱⁿʸ", Fonts.tiny),
    "comic": ("ᑕOᗰIᑕ", Fonts.comic),
    "san": ("𝗦𝗮𝗻𝘀 𝗕𝗼𝗹𝗱", Fonts.san),
    "slant_san": ("𝙎𝙖𝙣𝙨 𝘽𝙤𝙡𝙙", Fonts.slant_san),
    "slant": ("𝘚𝘢𝘯𝘴 𝘐𝘵𝘢𝘭𝘪𝘤", Fonts.slant),
    "sim": ("𝖲𝖺𝗇𝗌", Fonts.sim),
    "circles": ("ⒸⒾⓇⒸⓁⒺⓈ", Fonts.circles),
    "dark_circle": ("🅒🅘🅡🅒🅛🅔🅢", Fonts.dark_circle),
    "gothic": ("𝔊𝔬𝔱𝔥𝔦𝔠", Fonts.gothic),
    "bold_gothic": ("𝕲𝖔𝖙𝖍𝖎𝖈", Fonts.bold_gothic),
    "cloud": ("C͜͡l͜͡o͜͡u͜͡d͜͡", Fonts.cloud),
    "happy": ("H̆̈ă̈p̆̈p̆̈y̆̈", Fonts.happy),
    "sad": ("S̑̈ȃ̈d̑̈", Fonts.sad),
    "special": ("🇸 🇵 🇪 🇨 🇮 🇦 🇱", Fonts.special),
    "square": ("🄂🄀🄎🄀🅁🄴", Fonts.square),
    "dark_square": ("🆂🆀🆄🅰🆁🅴", Fonts.dark_square),
    "andalucia": ("ꪖꪀᦔꪖꪶꪊᥴ𝓲ꪖ", Fonts.andalucia),
    "manga": ("爪卂几ᘜ卂", Fonts.manga),
    "stinky": ("S̾t̾i̾n̾k̾y̾", Fonts.stinky),
    "bubbles": ("B̥ͦu̥ͦb̥ͦb̥ͦl̥ͦe̥ͦs̥ͦ", Fonts.bubbles),
    "underline": ("U͟n͟d͟e͟r͟l͟i͟n͟e͟", Fonts.underline),
    "ladybug": ("꒒ꍏꀷꌩꌃꀎꁅ", Fonts.ladybug),
    "rays": ("R҉a҉y҉s҉", Fonts.rays),
    "birds": ("B҈i҈r҈d҈s҈", Fonts.birds),
    "slash": ("S̸l̸a̸s̸h̸", Fonts.slash),
    "stop": ("s⃠t⃠o⃠p⃠", Fonts.stop),
    "skyline": ("S̺͆k̺͆y̺͆l̺͆i̺͆n̺͆e̺͆", Fonts.skyline),
    "arrows": ("A͎r͎r͎o͎w͎s͎", Fonts.arrows),
    "rvnes": ("ዪሀክቿነ", Fonts.rvnes),
    "strike": ("S̶t̶r̶i̶k̶e̶", Fonts.strike),
    "frozen": ("F༙r༙o༙z༙e༙n༙", Fonts.frozen),
}

BASE_STYLE_IDS = list(STYLE_MAP.keys())

# Clean visual treatments.  These are intentionally applied to the letters,
# rather than surrounding the whole name with repeated ornaments.
def _letters(text):
    return list(text)


def _spaced(text):
    return " ".join(_letters(text))  # thin-space, readable in Telegram


def _dots(text):
    return " • ".join(_letters(text))


def _overline(text):
    return "".join(ch + "\u0305" if ch.strip() else ch for ch in text)


def _lowline(text):
    return "".join(ch + "\u0332" if ch.strip() else ch for ch in text)


def _strike(text):
    return "".join(ch + "\u0336" if ch.strip() else ch for ch in text)


def _slash(text):
    return "".join(ch + "\u0338" if ch.strip() else ch for ch in text)


def _doubleline(text):
    return "".join(ch + "\u0333" if ch.strip() else ch for ch in text)


def _boxed(text):
    return f"『{text}』"


def _angle(text):
    return f"‹ {text} ›"


def _variant_specs(count, modes):
    out = []
    for base_index, base_id in enumerate(BASE_STYLE_IDS):
        for mode_name, mode_fn in modes:
            out.append((base_id, mode_name, mode_fn))
            if len(out) >= count:
                return out
    return out


# Each category is made from the actual font converters first. The extra modes
# create genuine, visually distinct variants without turning every style into
# the same heavy decoration.
FONT_MODES = [
    ("Standard", lambda x: x),
    ("Spaced", _spaced),
    ("Dotted", _dots),
    ("Overline", _overline),
]
AESTHETIC_MODES = [
    ("Standard", lambda x: x),
    ("Spaced", _spaced),
    ("Lowline", _lowline),
]
LIVE_MODES = [
    ("Standard", lambda x: x),
    ("Slash", _slash),
    ("Strike", _strike),
]


def _build_font_variants(count, modes, prefix):
    specs = _variant_specs(count, modes)
    variants = []
    for index, (base_id, mode_name, mode_fn) in enumerate(specs):
        label, converter = STYLE_MAP[base_id]
        def make_converter(base_converter=converter, modifier=mode_fn):
            def convert(text):
                return modifier(base_converter(text))
            return convert
        converter_fn = make_converter()
        variants.append({
            "id": f"{prefix}{index}",
            "base": base_id,
            "converter": converter_fn,
            "template": "{x}",
            "sample": converter_fn("Jisan"),
            "name": label if mode_name == "Standard" else f"{label} • {mode_name}",
        })
    return variants


NAME_STYLES = {
    # Keep the large page counts of the reference layout, while the buttons use
    # distinct font faces instead of repeating one decorative wrapper.
    "premium": _build_font_variants(156, FONT_MODES, "P"),
    "aesthetic": _build_font_variants(107, AESTHETIC_MODES, "A"),
    "live": _build_font_variants(15, LIVE_MODES, "L"),
}

# Bangla does not have a full Unicode equivalent of Latin mathematical bold/
# script alphabets.  These are therefore clean Bangla display variants, using
# the user's exact Bangla text without replacing it with Hindi/Devanagari.
BANGLA_STYLES = [
    ("Simple", "{x}"),
    ("Soft", "♡ {x} ♡"),
    ("Flower", "🌷 {x} 🌷"),
    ("Cloud", "☁️ {x} ☁️"),
    ("Elegant", "『 {x} 』"),
    ("Classic", "꧁༺ {x} ༻꧂"),
    ("Crown", "♛ {x} ♛"),
    ("Spark", "✦ {x} ✦"),
    ("Star", "★ {x} ★"),
    ("Aesthetic", "୨୧ {x} ୨୧"),
    ("Diamond", "◇ {x} ◇"),
    ("Arrow", "➳ {x} ➳"),
    ("Wave", "〰 {x} 〰"),
    ("Leaf", "❀ {x} ❀"),
    ("Frame", "【 {x} 】"),
    ("Round", "〔 {x} 〕"),
    ("Angle", "‹ {x} ›"),
    ("Double", "《 {x} 》"),
    ("Royal", "༺♛ {x} ♛༻"),
    ("Cute", "૮ ˶ᵔ ᵕ ᵔ˶ ა {x}"),
]

NAME_STYLES["bangla"] = []
for index, (name, template) in enumerate(BANGLA_STYLES):
    NAME_STYLES["bangla"].append({
        "id": f"B{index}",
        "base": "bangla",
        "converter": lambda text: text,
        "template": template,
        "sample": template.format(x="জিসান"),
        "name": f"Bangla • {name}",
    })

CATEGORY_TITLES = {
    "premium": "👑 PREMIUM DESIGN",
    "aesthetic": "✨ Aesthetic Art Styles",
    "live": "🎬 Live Design",
    "bangla": "🇧🇩 Bangla Live Design",
}


# ----------------------- NAME RENDERING -------------------
def apply_variant(variant, text):
    try:
        styled = variant["converter"](text)
    except Exception:
        styled = text
    return variant["template"].format(x=styled)


def sample_variant(variant):
    return variant["sample"]


def page_keyboard(category, page=0, preview_name="Jisan"):
    variants = NAME_STYLES[category]
    per_page = 10
    total_pages = max(1, (len(variants) + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))
    start = page * per_page
    chunk = variants[start:start + per_page]
    rows = []

    for row_start in range(0, len(chunk), 2):
        row = []
        for local_index, variant in enumerate(chunk[row_start:row_start + 2], row_start):
            global_index = start + local_index
            preview = apply_variant(variant, preview_name)
            if len(preview) > 26:
                preview = preview[:26].rstrip() + "…"
            row.append(InlineKeyboardButton(
                f"{global_index + 1}. {preview}",
                callback_data=f"style|{category}|{page}|{global_index}"
            ))
        rows.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"page|{category}|{page - 1}"))
    nav.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"page|{category}|{page + 1}"))
    rows.append(nav)
    rows.append([
        InlineKeyboardButton("⬅️ Back", callback_data="categories"),
        InlineKeyboardButton("✏️ New Name", callback_data="menu_name"),
        InlineKeyboardButton("🏠 Main Menu", callback_data="home"),
    ])
    return InlineKeyboardMarkup(rows)


def selected_keyboard(category, page, variant_index):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 Copy Code", callback_data=f"copy|{category}|{page}|{variant_index}"),
            InlineKeyboardButton("📝 Edit Components", callback_data=f"edit|{category}|{page}|{variant_index}"),
        ],
        [
            InlineKeyboardButton("⬅️ Back", callback_data=f"page|{category}|{page}"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="home"),
        ],
    ])


def welcome_text():
    total = sum(len(items) for items in NAME_STYLES.values())
    return f"""✨ **Welcome to Stylish Name Maker Bot!** ✨

👑 **VIP Premium & Aesthetic Name Studio**

───────────────

🎨 **{total}+ Stylish Name Variants**
📝 **Aesthetic, Attitude, Love & Islamic Bio Maker**
🚀 **Bulk Name Generator**

───────────────

👇 **Niche diye gaye buttons se option select karein:** 👇"""


# ------------------------- BIO MODULE ---------------------
BIO_CATEGORIES = {
    "aesthetic": "✨ Aesthetic Bio",
    "attitude": "👑 Attitude Bio",
    "love": "💗 Love Bio",
    "islamic": "🕌 Islamic Bio",
    "simple": "🌷 Simple Bio",
}

BIO_TEMPLATES = {
    "aesthetic": [
        "☁️ Lost in little moments, finding beauty everywhere. 🌷",
        "🌙 Quiet soul • Soft heart • Peaceful mind ✨",
        "🦋 Growing silently, glowing naturally. ☁️",
        "🌷 Simple life, pretty thoughts, peaceful vibes.",
        "✨ Creating my own little world, one day at a time. 🤍",
    ],
    "attitude": [
        "👑 I know my worth, so I don't chase approval.",
        "🖤 Calm face • Clear mind • Strong boundaries.",
        "⚡ Less talk, more focus. That's the vibe.",
        "👑 Respect is mutual. Energy is returned.",
        "🕶️ Not here to impress, just here to be myself.",
    ],
    "love": [
        "💗 A little love can make an ordinary day beautiful.",
        "🌷 Some people simply make life feel warmer. 🤍",
        "✨ Heart full of memories, eyes full of dreams.",
        "🫶 Love softly, care deeply, stay genuine.",
        "🌙 You are a beautiful chapter in my story. 💗",
    ],
    "islamic": [
        "🕌 Alhamdulillah for everything, always. 🤍",
        "🌙 Sabr • Shukr • Tawakkul ✨",
        "🤲 Allah knows what the heart cannot explain.",
        "🕊️ Keep your heart close to Allah and your hopes alive.",
        "☪️ What Allah has written for you will never miss you.",
    ],
    "simple": [
        "🌷 Just me, living one day at a time.",
        "☁️ Peace over pressure.",
        "✨ Be real. Stay kind. Keep growing.",
        "🤍 Small circle, peaceful life.",
        "🌿 Simple mind, happy heart.",
    ],
}


def bio_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ Aesthetic Bio", callback_data="bio_cat|aesthetic")],
        [InlineKeyboardButton("👑 Attitude Bio", callback_data="bio_cat|attitude")],
        [InlineKeyboardButton("💗 Love Bio", callback_data="bio_cat|love")],
        [InlineKeyboardButton("🕌 Islamic Bio", callback_data="bio_cat|islamic")],
        [InlineKeyboardButton("🌷 Simple Bio", callback_data="bio_cat|simple")],
        [InlineKeyboardButton("✍️ Custom Bio", callback_data="bio_custom")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="home")],
    ])


def bio_result_keyboard(category, custom=False):
    rows = []
    if not custom:
        rows.append([InlineKeyboardButton("🔄 Another Bio", callback_data=f"bio_cat|{category}")])
    rows.extend([
        [InlineKeyboardButton("✍️ Custom Bio", callback_data="bio_custom")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="home")],
    ])
    return InlineKeyboardMarkup(rows)


# ------------------------- BULK MODULE --------------------
def bulk_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👑 Premium Style", callback_data="bulk_style|premium")],
        [InlineKeyboardButton("✨ Aesthetic Style", callback_data="bulk_style|aesthetic")],
        [InlineKeyboardButton("🎬 Live Style", callback_data="bulk_style|live")],
        [InlineKeyboardButton("🇧🇩 Bangla Style", callback_data="bulk_style|bangla")],
        [InlineKeyboardButton("📝 Enter Names Again", callback_data="menu_bulk")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="home")],
    ])


def bulk_style_picker(group):
    variants = NAME_STYLES[group]
    # Keep the bulk menu compact: 12 representative variants from the category.
    picks = variants[:12]
    rows = []
    for i in range(0, len(picks), 2):
        row = []
        for offset, variant in enumerate(picks[i:i + 2]):
            num = i + offset + 1
            row.append(InlineKeyboardButton(
                f"{num}. {sample_variant(variant)[:20]}",
                callback_data=f"bulk_font|{group}|{i + offset}"
            ))
        rows.append(row)
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data="bulk_back")])
    return InlineKeyboardMarkup(rows)


def render_bulk(names, group, variant_index):
    variants = NAME_STYLES.get(group, [])
    if not (0 <= variant_index < len(variants)):
        return ""
    variant = variants[variant_index]
    output = []
    for index, name in enumerate(names, 1):
        output.append(f"{index}. {apply_variant(variant, name)}")
    return "\n".join(output)


# ------------------------- START/HELP ---------------------
async def start(c, m):
    uid = m.from_user.id
    USER_STATE.pop(uid, None)
    await m.reply_text(welcome_text(), reply_markup=main_menu(), quote=True)


async def help_command(c, m):
    text = """❓ **How To Use**

✏️ **Make My Name** — create stylish name variants
📝 **BIO** — generate aesthetic, attitude, love, Islamic or simple bios
🚀 **Bulk Names** — style multiple names together

💡 **Tip:** A category shows 10 styles per page. Tap **Next ➡️** to browse more."""
    await m.reply_text(text, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Make My Name", callback_data="menu_name")],
        [InlineKeyboardButton("📝 BIO", callback_data="menu_bio")],
        [InlineKeyboardButton("🚀 Bulk Names", callback_data="menu_bulk")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="home")],
    ]))


# ------------------------- TEXT INPUT ---------------------
async def receive_text(c, m):
    uid = m.from_user.id
    state = USER_STATE.get(uid, "")
    text = m.text.strip()

    if not text:
        await m.reply_text("❌ Please send some text.")
        return

    # Name input / name edit
    if state == "waiting_name" or state.startswith("editing:"):
        if len(text) > 100:
            await m.reply_text("❌ Name is too long. Please keep it within 100 characters.")
            return

        USER_NAME[uid] = text
        if state.startswith("editing:"):
            _, category, page_s, index_s = state.split(":", 3)
            try:
                variant_index = int(index_s)
                variant = NAME_STYLES[category][variant_index]
            except (ValueError, KeyError, IndexError):
                variant = None

            if variant is not None:
                styled = apply_variant(variant, text)
                USER_STATE[uid] = f"selected:{category}:{page_s}:{variant_index}"
                await m.reply_text(
                    f"✨ **Updated Design:**\n\n{styled}\n\n"
                    "Edit ya copy ke liye buttons use karein:",
                    reply_markup=selected_keyboard(category, int(page_s), variant_index),
                    quote=True,
                )
                await m.reply_text(styled)
                return

        USER_STATE[uid] = "categories"
        await m.reply_text(
            f"✅ **Name:** {text}\n\n"
            "👇 **Kripya Niche Diye Gaye 4 Category Sections Me Se Select Karein:** 👇",
            reply_markup=category_menu(),
            quote=True,
        )
        return

    # Custom bio input
    if state == "waiting_custom_bio":
        if len(text) > 500:
            await m.reply_text("❌ Bio is too long. Please keep it within 500 characters.")
            return
        USER_BIO[uid] = text
        USER_STATE[uid] = "bio_result"
        await m.reply_text(
            f"📝 **Your Custom Bio**\n\n{text}",
            reply_markup=bio_result_keyboard("custom", custom=True),
            quote=True,
        )
        await m.reply_text(text)
        return

    # Bulk names input
    if state == "waiting_bulk_names":
        raw = text.replace(",", "\n")
        names = [line.strip() for line in raw.splitlines() if line.strip()]
        if not names:
            await m.reply_text("❌ Send at least one name.")
            return
        if len(names) > 30:
            await m.reply_text("❌ Maximum 30 names per batch.")
            return
        names = [name[:100] for name in names]
        USER_BULK[uid] = names
        USER_STATE[uid] = "bulk_style"
        await m.reply_text(
            f"🚀 **Bulk Names Ready**\n\n"
            f"👥 {len(names)} names received.\n\n"
            "👇 Choose a style section:",
            reply_markup=bulk_menu(),
            quote=True,
        )
        return


# ------------------------- CALLBACKS ---------------------
async def callbacks(c, q):
    uid = q.from_user.id
    data = q.data or ""

    if data == "noop":
        await q.answer()
        return

    if data == "home":
        USER_STATE[uid] = "home"
        await q.answer()
        await q.message.edit_text(welcome_text(), reply_markup=main_menu())
        return

    if data == "menu_name":
        USER_STATE[uid] = "waiting_name"
        await q.answer("Send your name ✨")
        await q.message.edit_text(
            "✏️ **Make My Name**\n\nSend me the name you want to style.\n\nExample: `Jisan`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Main Menu", callback_data="home")]
            ]),
        )
        return

    if data == "categories":
        if uid not in USER_NAME:
            USER_STATE[uid] = "waiting_name"
            await q.answer("Please send your name first.", show_alert=True)
            return
        USER_STATE[uid] = "categories"
        await q.answer()
        await q.message.edit_text(
            f"✅ **Name:** {USER_NAME[uid]}\n\n"
            "👇 **Kripya Niche Diye Gaye 4 Category Sections Me Se Select Karein:** 👇",
            reply_markup=category_menu(),
        )
        return

    if data == "menu_help":
        await q.answer()
        await q.message.edit_text(
            "❓ **Help**\n\n"
            "✏️ Make My Name — stylish names\n"
            "📝 BIO — ready-made & custom bios\n"
            "🚀 Bulk Names — style up to 30 names together\n\n"
            "💡 Each name category has paginated style variants.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ Make My Name", callback_data="menu_name")],
                [InlineKeyboardButton("📝 BIO", callback_data="menu_bio")],
                [InlineKeyboardButton("🚀 Bulk Names", callback_data="menu_bulk")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="home")],
            ]),
        )
        return

    # ---------------- BIO ----------------
    if data == "menu_bio":
        USER_STATE[uid] = "bio_menu"
        await q.answer()
        await q.message.edit_text(
            "📝 **BIO MAKER**\n\n"
            "Choose a bio category below ✨\n"
            "You can also write your own custom bio.",
            reply_markup=bio_menu(),
        )
        return

    if data == "bio_custom":
        USER_STATE[uid] = "waiting_custom_bio"
        await q.answer("Send your custom bio ✍️")
        await q.message.edit_text(
            "✍️ **Custom Bio**\n\n"
            "Send the bio/text you want to use.\n\n"
            "Maximum: 500 characters.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back", callback_data="menu_bio")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="home")],
            ]),
        )
        return

    if data.startswith("bio_cat|"):
        category = data.split("|", 1)[1]
        if category not in BIO_TEMPLATES:
            await q.answer("Category not found.", show_alert=True)
            return
        key = f"bio_index:{category}"
        old_index = USER_STATE.get(key, -1)
        if not isinstance(old_index, int):
            old_index = -1
        index = (old_index + 1) % len(BIO_TEMPLATES[category])
        USER_STATE[key] = index
        bio = BIO_TEMPLATES[category][index]
        USER_BIO[uid] = bio
        USER_STATE[uid] = f"bio_result:{category}"
        await q.answer("Bio generated ✨")
        await q.message.edit_text(
            f"📝 **{BIO_CATEGORIES[category]}**\n\n{bio}",
            reply_markup=bio_result_keyboard(category),
        )
        await q.message.reply_text(bio)
        return

    # ---------------- BULK ----------------
    if data == "menu_bulk":
        USER_STATE[uid] = "waiting_bulk_names"
        await q.answer("Send your names 🚀")
        await q.message.edit_text(
            "🚀 **BULK NAME MAKER**\n\n"
            "Send multiple names, one per line.\n"
            "You can also separate them with commas.\n\n"
            "Example:\n"
            "Jisan\n"
            "Rahim\n"
            "Karim\n\n"
            "📌 Maximum 30 names per batch.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Main Menu", callback_data="home")]
            ]),
        )
        return

    if data == "bulk_back":
        USER_STATE[uid] = "bulk_style"
        await q.answer()
        await q.message.edit_text(
            f"🚀 **Bulk Names**\n\n👥 {len(USER_BULK.get(uid, []))} names loaded.\n\nChoose a style section:",
            reply_markup=bulk_menu(),
        )
        return

    if data.startswith("bulk_style|"):
        group = data.split("|", 1)[1]
        if group not in NAME_STYLES or not USER_BULK.get(uid):
            await q.answer("Please enter your names first.", show_alert=True)
            return
        USER_STATE[uid] = f"bulk_picker:{group}"
        await q.answer()
        await q.message.edit_text(
            f"🚀 **Bulk Style Picker**\n\n"
            f"👥 {len(USER_BULK[uid])} names\n"
            f"📂 {CATEGORY_TITLES[group]}\n\n"
            "👇 Select the exact style:",
            reply_markup=bulk_style_picker(group),
        )
        return

    if data.startswith("bulk_font|"):
        _, group, index_s = data.split("|", 2)
        try:
            variant_index = int(index_s)
        except ValueError:
            await q.answer("Style not found.", show_alert=True)
            return
        if group not in NAME_STYLES or variant_index >= len(NAME_STYLES[group]) or not USER_BULK.get(uid):
            await q.answer("Bulk data expired. Please start again.", show_alert=True)
            return
        result = render_bulk(USER_BULK[uid], group, variant_index)
        USER_STATE[uid] = f"bulk_result:{group}:{variant_index}"
        await q.answer("Bulk names generated ✨")
        await q.message.edit_text(
            f"🚀 **Bulk Result**\n\n{result}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Choose Another Style", callback_data="bulk_back")],
                [InlineKeyboardButton("📝 New Bulk Names", callback_data="menu_bulk")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="home")],
            ]),
        )
        return

    # ---------------- NAME CATEGORIES ----------------
    if data.startswith("cat_"):
        category = data[4:]
        if category not in NAME_STYLES:
            await q.answer("Unknown category.", show_alert=True)
            return
        if uid not in USER_NAME:
            await q.answer("Please send a name first.", show_alert=True)
            return
        USER_STATE[uid] = f"category:{category}:0"
        await q.answer()
        styles = NAME_STYLES[category]
        await q.message.edit_text(
            f"✨ **{CATEGORY_TITLES[category]}**\n\n"
            f"👤 Name: {USER_NAME[uid]}\n"
            f"🎨 **{len(styles)} Style Variants**\n\n"
            "👇 **Click on any style below to view your design:**",
            reply_markup=page_keyboard(category, 0, USER_NAME[uid]),
        )
        return

    if data.startswith("page|"):
        _, category, page_s = data.split("|", 2)
        try:
            page = int(page_s)
        except ValueError:
            await q.answer("Page error.", show_alert=True)
            return
        if category not in NAME_STYLES or uid not in USER_NAME:
            await q.answer("Please start again.", show_alert=True)
            return
        USER_STATE[uid] = f"category:{category}:{page}"
        await q.answer()
        await q.message.edit_text(
            f"✨ **{CATEGORY_TITLES[category]}**\n\n"
            f"👤 Name: {USER_NAME[uid]}\n"
            f"🎨 **{len(NAME_STYLES[category])} Style Variants**\n\n"
            "👇 **Click on any style below to view your design:**",
            reply_markup=page_keyboard(category, page, USER_NAME[uid]),
        )
        return

    if data.startswith("style|"):
        _, category, page_s, index_s = data.split("|", 3)
        try:
            page = int(page_s)
            variant_index = int(index_s)
            variant = NAME_STYLES[category][variant_index]
        except (ValueError, KeyError, IndexError):
            await q.answer("Style not found.", show_alert=True)
            return
        name = USER_NAME.get(uid)
        if not name:
            await q.answer("Please enter your name first.", show_alert=True)
            return
        styled = apply_variant(variant, name)
        USER_STATE[uid] = f"selected:{category}:{page}:{variant_index}"
        await q.answer()
        await q.message.edit_text(
            f"✨ **Aapka Selected Design:**\n\n{styled}\n\n"
            "Edit ya copy ke liye buttons use karein:",
            reply_markup=selected_keyboard(category, page, variant_index),
        )
        await q.message.reply_text(styled)
        return

    if data.startswith("copy|"):
        _, category, page_s, index_s = data.split("|", 3)
        try:
            variant_index = int(index_s)
            variant = NAME_STYLES[category][variant_index]
        except (ValueError, KeyError, IndexError):
            await q.answer("Please start again.", show_alert=True)
            return
        name = USER_NAME.get(uid)
        if not name:
            await q.answer("Please start again.", show_alert=True)
            return
        styled = apply_variant(variant, name)
        await q.answer("Copy-ready text sent below ✨")
        await q.message.reply_text(styled)
        return

    if data.startswith("edit|"):
        _, category, page_s, index_s = data.split("|", 3)
        USER_STATE[uid] = f"editing:{category}:{page_s}:{index_s}"
        await q.answer("Send the new name ✨")
        await q.message.edit_text(
            "📝 **Edit Components**\n\n"
            "Send the new name/text you want to use.\n\n"
            "Example: `Jisan`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back", callback_data=f"page|{category}|{page_s}")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="home")],
            ]),
        )
        return

    await q.answer()


# -------------------- HANDLER REGISTRATION --------------------
def register_handlers(app):
    """Register all bot handlers directly on the Pyrogram Client."""
    app.add_handler(MessageHandler(start, filters.command("start") & filters.private))
    app.add_handler(MessageHandler(help_command, filters.command("help") & filters.private))
    app.add_handler(
        MessageHandler(
            receive_text,
            filters.private & filters.text & ~filters.command(["start", "help"]),
        )
    )
    app.add_handler(CallbackQueryHandler(callbacks))
