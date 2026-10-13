"""Stylish Name Maker — dynamic Telegram bot with a private admin panel.

Style/category/UI content is stored in Firebase Realtime Database when configured.
Without Firebase, local JSON storage is used for testing only (Render local files can reset).
"""
from __future__ import annotations

import copy
import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CopyTextButton,
    InputFile,
    BotCommand,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

try:
    import firebase_admin
    from firebase_admin import credentials, db
except ImportError:  # Firebase is optional for local smoke testing.
    firebase_admin = None
    credentials = None
    db = None

# ----------------------------- Configuration -----------------------------
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
)
logger = logging.getLogger("stylish-name-maker")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = {
    int(item.strip())
    for item in os.getenv("ADMIN_IDS", "8223664417,8819766785").split(",")
    if item.strip().isdigit()
}
FIREBASE_DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL", "").strip()
FIREBASE_CREDENTIALS_JSON = os.getenv("FIREBASE_CREDENTIALS_JSON", "").strip()
DATA_FILE = Path(os.getenv("DATA_FILE", "data/bot_data.json"))
DB_PATH = "/stylish_name_maker"

# These are only fallback interface strings. Admin-edited values are stored in the database.
DEFAULT_TEXTS: dict[str, str] = {
    "welcome": (
        "✦ 𝗦𝗧𝗬𝗟𝗜𝗦𝗛 𝗡𝗔𝗠𝗘 𝗠𝗔𝗞𝗘𝗥 ✦\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "তোমার নামকে দাও নিজের মতো একটি সুন্দর স্টাইল।\n\n"
        "✧ Name • Bio • Bulk Names\n"
        "✧ Premium • Aesthetic • Elegant\n"
        "✧ Copy-ready Unicode styles"
    ),
    "action_prompt": "👇 নিচের অপশন থেকে বেছে নাও:",
    "ask_name": "✍️ যে নামটি স্টাইল করতে চাও, সেটি পাঠাও।",
    "ask_bio": "📝 যে Bio বা টেক্সটটি সাজাতে চাও, সেটি পাঠাও।",
    "ask_bulk": "🚀 একসঙ্গে একাধিক নাম পাঠাও। প্রতিটি নাম নতুন লাইনে লিখবে (সর্বোচ্চ ৮টি)।",
    "category_intro": "✅ ইনপুট: {input}\n\n👇 পছন্দের Style Collection বেছে নাও:",
    "help": (
        "✦ 𝗛𝗘𝗟𝗣 & 𝗚𝗨𝗜𝗗𝗘 ✦\n\n"
        "✏️ Make My Name — একটি নামের জন্য\n"
        "📝 BIO — Bio বা সাধারণ টেক্সটের জন্য\n"
        "🚀 Bulk Names — একসঙ্গে সর্বোচ্চ ৮টি নাম\n\n"
        "একটি Collection বেছে নাও, তারপর পেজ ধরে স্টাইল দেখো। ছোট ফলাফলের পাশে Copy বাটন থাকবে।\n\n"
        "স্টাইলের তালিকা ও Collection সময়ের সঙ্গে Admin Panel থেকে পরিবর্তন করা হয়।"
    ),
    "empty_categories": (
        "এখনো কোনো Style Collection তৈরি করা হয়নি।\n\n"
        "Admin-কে বলো Style যোগ করতে বা JSON style pack import করতে।"
    ),
    "empty_styles": "এই Collection-এ এখনো কোনো চালু Style নেই। অন্য Collection দেখো বা Admin-কে জানাও।",
    "style_heading": "✦ {category} ✦",
    "style_page_info": "Page {page}/{pages}  •  {count} styles",
    "style_divider": "━━━━━━━━━━━━━━━━━━",
    "category_button_template": "{category} ({count} styles)",
    "btn_copy_prefix": "📋 Copy #",
    "btn_collections": "↩️ Collections",
    "btn_results_home": "🏠 Main Menu",
    "btn_style_prev": "⬅️ Previous",
    "btn_style_next": "Next ➡️",
    "admin_title": "✦ 𝗔𝗗𝗠𝗜𝗡 𝗖𝗢𝗡𝗧𝗥𝗢𝗟 𝗖𝗘𝗡𝗧𝗘𝗥 ✦",
    "admin_intro": "নিচের বাটন থেকে বেছে নাও। Style/UI data ডেটাবেসে সেভ হবে—সাধারণ পরিবর্তনে redeploy লাগবে না।",
    "btn_name": "✏️ Make My Name",
    "btn_bio": "📝 BIO",
    "btn_bulk": "🚀 Bulk Names",
    "btn_help": "❔ Help",
    "btn_main_menu": "🏠 Main Menu",
    "btn_new_name": "✏️ New Name",
    "btn_admin": "🛠 Admin Panel",
    "btn_add_style": "➕ Add Style",
    "btn_import_json": "📥 Import JSON",
    "btn_export_json": "📤 Export JSON",
    "btn_manage_styles": "🧩 Manage Styles",
    "btn_manage_categories": "🗂 Manage Categories",
    "btn_edit_texts": "📝 Edit UI Texts",
    "btn_stats": "📊 Statistics",
    "btn_back": "⬅️ Back",
    "btn_cancel": "✖️ Cancel",
    "btn_add_category": "➕ Add Category",
    "btn_cat_prev": "⬅️ Previous",
    "btn_cat_next": "Next ➡️",
}

TEXT_LABELS: dict[str, str] = {
    "welcome": "Welcome Message",
    "action_prompt": "Main Menu Prompt",
    "ask_name": "Name Input Prompt",
    "ask_bio": "Bio Input Prompt",
    "ask_bulk": "Bulk Names Prompt",
    "category_intro": "Category Selection Message",
    "help": "Help Message",
    "empty_categories": "Empty Categories Message",
    "empty_styles": "Empty Styles Message",
    "style_heading": "Style Results Heading",
    "style_page_info": "Style Page Counter",
    "style_divider": "Style Divider",
    "category_button_template": "Category Button Format",
    "btn_copy_prefix": "Copy Button Prefix",
    "btn_collections": "Collections Button",
    "btn_results_home": "Results Main Menu Button",
    "btn_style_prev": "Previous Styles Button",
    "btn_style_next": "Next Styles Button",
    "admin_title": "Admin Panel Heading",
    "admin_intro": "Admin Panel Intro",
    "btn_name": "Main Button — Make My Name",
    "btn_bio": "Main Button — BIO",
    "btn_bulk": "Main Button — Bulk Names",
    "btn_help": "Main Button — Help",
    "btn_main_menu": "Main Menu Button",
    "btn_new_name": "New Name Button",
    "btn_admin": "Admin Panel Button",
    "btn_add_style": "Admin Button — Add Style",
    "btn_import_json": "Admin Button — Import JSON",
    "btn_export_json": "Admin Button — Export JSON",
    "btn_manage_styles": "Admin Button — Manage Styles",
    "btn_manage_categories": "Admin Button — Manage Categories",
    "btn_edit_texts": "Admin Button — Edit UI Texts",
    "btn_stats": "Admin Button — Statistics",
    "btn_back": "Back Button",
    "btn_cancel": "Cancel Button",
    "btn_add_category": "Admin Button — Add Category",
    "btn_cat_prev": "Previous Categories Button",
    "btn_cat_next": "Next Categories Button",
}

TRANSFORM_LABELS: dict[str, str] = {
    "none": "Plain / Wrapper only",
    "bold": "Bold Serif",
    "italic": "Italic Serif",
    "bold_italic": "Bold Italic",
    "script": "Elegant Script",
    "script_bold": "Bold Script",
    "fraktur": "Fraktur",
    "double_struck": "Double-Struck",
    "sans": "Sans Serif",
    "sans_bold": "Sans Bold",
    "sans_italic": "Sans Italic",
    "monospace": "Monospace",
    "small_caps": "Small Caps",
    "fullwidth": "Fullwidth",
}


def _font_map(upper: str, lower: str, digits: str | None = None) -> dict[str, str]:
    mapping: dict[str, str] = {}
    src_upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    src_lower = "abcdefghijklmnopqrstuvwxyz"
    if len(upper) == len(src_upper):
        mapping.update(zip(src_upper, upper))
    if len(lower) == len(src_lower):
        mapping.update(zip(src_lower, lower))
    if digits and len(digits) == 10:
        mapping.update(zip("0123456789", digits))
    return mapping


FONT_MAPS: dict[str, dict[str, str]] = {
    "bold": _font_map(
        "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙",
        "𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳",
        "𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗",
    ),
    "italic": _font_map(
        "𝐴𝐵𝐶𝐷𝐸𝐹𝐺𝐻𝐼𝐽𝐾𝐿𝑀𝑁𝑂𝑃𝑄𝑅𝑆𝑇𝑈𝑉𝑊𝑋𝑌𝑍",
        "𝑎𝑏𝑐𝑑𝑒𝑓𝑔𝑕𝑖𝑗𝑘𝑙𝑚𝑛𝑜𝑝𝑞𝑟𝑠𝑡𝑢𝑣𝑤𝑥𝑦𝑧",
    ),
    "bold_italic": _font_map(
        "𝑨𝑩𝑪𝑫𝑬𝑭𝑮𝑯𝑰𝑱𝑲𝑳𝑴𝑵𝑶𝑷𝑸𝑹𝑺𝑻𝑼𝑽𝑾𝑿𝒀𝒁",
        "𝒂𝒃𝒄𝒅𝒆𝒇𝒈𝒉𝒊𝒋𝒌𝒍𝒎𝒏𝒐𝒑𝒒𝒓𝒔𝒕𝒖𝒗𝒘𝒙𝒚𝒛",
    ),
    "script": _font_map(
        "𝒜ℬ𝒞𝒟ℰℱ𝒢ℋℐ𝒥𝒦ℒℳ𝒩𝒪𝒫𝒬ℛ𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵",
        "𝒶𝒷𝒸𝒹ℯ𝒻ℊ𝒽𝒾𝒿𝓀𝓁𝓂𝓃ℴ𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏",
    ),
    "script_bold": _font_map(
        "𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩",
        "𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃",
    ),
    "fraktur": _font_map(
        "𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ",
        "𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶𝔷",
    ),
    "double_struck": _font_map(
        "𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ",
        "𝕒𝕓𝕔𝕕𝕖𝕗𝕘𝕙𝕚𝕛𝕜𝕝𝕞𝕟𝕠𝕡𝕢𝕣𝕤𝕥𝕦𝕧𝕨𝕩𝕪𝕫",
    ),
    "sans": _font_map(
        "𝖠𝖡𝖢𝖣𝖤𝖥𝖦𝖧𝖨𝖩𝖪𝖫𝖬𝖭𝖮𝖯𝖰𝖱𝖲𝖳𝖴𝖵𝖶𝖷𝖸𝖹",
        "𝖺𝖻𝖼𝖽𝖾𝖿𝗀𝗁𝗂𝗃𝗄𝗅𝗆𝗇𝗈𝗉𝗊𝗋𝗌𝗍𝗎𝗏𝗐𝗑𝗒𝗓",
    ),
    "sans_bold": _font_map(
        "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭",
        "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇",
        "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵",
    ),
    "sans_italic": _font_map(
        "𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡",
        "𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻",
    ),
    "monospace": _font_map(
        "𝙰𝙱𝙲𝙳𝙴𝙵𝙶𝙷𝙸𝙹𝙺𝙻𝙼𝙽𝙾𝙿𝚀𝚁𝚂𝚃𝚄𝚅𝚆𝚇𝚈𝚉",
        "𝚊𝚋𝚌𝚍𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝚚𝚛𝚜𝚝𝚞𝚟𝚠𝚡𝚢𝚣",
        "𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿",
    ),
    "fullwidth": _font_map(
        "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ",
        "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ",
        "０１２３４５６７８９",
    ),
    "small_caps": dict(zip(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ".lower() + "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ",
    )),
}
# Small-caps should render uppercase/lowercase to a readable small-cap set.
FONT_MAPS["small_caps"] = dict(zip(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
    "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ",
))

# ----------------------------- Data storage ------------------------------
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def empty_data() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "categories": {},
        "styles": {},
        "texts": copy.deepcopy(DEFAULT_TEXTS),
        "users": {},
        "usage": {"generated": 0, "bulk_jobs": 0},
    }


class DataStore:
    """Firebase Realtime Database when configured; local JSON only as a dev fallback."""
    def __init__(self) -> None:
        self.firebase_ref = None
        self.local_mode = True
        if FIREBASE_DATABASE_URL and FIREBASE_CREDENTIALS_JSON and firebase_admin is not None:
            try:
                service_account = json.loads(FIREBASE_CREDENTIALS_JSON)
                if not firebase_admin._apps:
                    cred = credentials.Certificate(service_account)
                    firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DATABASE_URL})
                self.firebase_ref = db.reference(DB_PATH)
                self.local_mode = False
                logger.info("Firebase Realtime Database enabled at %s", DB_PATH)
            except Exception as exc:
                logger.exception("Firebase setup failed; local JSON fallback enabled: %s", exc)
        else:
            logger.warning(
                "Firebase is not configured. Local JSON mode is for testing only; configure "
                "FIREBASE_DATABASE_URL and FIREBASE_CREDENTIALS_JSON for persistent Render storage."
            )
        if self.local_mode:
            DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
            if not DATA_FILE.exists():
                DATA_FILE.write_text(json.dumps(empty_data(), ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self) -> dict[str, Any]:
        raw: Any = None
        try:
            if self.firebase_ref is not None:
                raw = self.firebase_ref.get()
            else:
                raw = json.loads(DATA_FILE.read_text(encoding="utf-8")) if DATA_FILE.exists() else None
        except Exception as exc:
            logger.exception("Could not read database: %s", exc)
        if not isinstance(raw, dict):
            data = empty_data()
            self.save(data)
            return data
        base = empty_data()
        for key in ("categories", "styles", "users", "usage"):
            if isinstance(raw.get(key), dict):
                base[key] = raw[key]
        if isinstance(raw.get("texts"), dict):
            base["texts"].update({k: str(v) for k, v in raw["texts"].items() if isinstance(v, str)})
        base["schema_version"] = 1
        return base

    def save(self, data: dict[str, Any]) -> None:
        try:
            if self.firebase_ref is not None:
                self.firebase_ref.set(data)
            else:
                DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
                temp = DATA_FILE.with_suffix(".tmp")
                temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                temp.replace(DATA_FILE)
        except Exception as exc:
            logger.exception("Could not save database: %s", exc)
            raise


STORE = DataStore()


def tx(data: dict[str, Any], key: str, **values: str) -> str:
    template = str(data.get("texts", {}).get(key, DEFAULT_TEXTS.get(key, key)))
    for name, value in values.items():
        template = template.replace("{" + name + "}", value)
    return template


def is_admin(user_id: int | None) -> bool:
    return user_id is not None and user_id in ADMIN_IDS


def ensure_private(update: Update) -> bool:
    return bool(update.effective_chat and update.effective_chat.type == "private")


def user_keyboard(data: dict[str, Any], user_id: int) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(tx(data, "btn_name"), style="primary"), KeyboardButton(tx(data, "btn_bio"), style="success")],
        [KeyboardButton(tx(data, "btn_bulk"), style="primary"), KeyboardButton(tx(data, "btn_help"), style="success")],
    ]
    if is_admin(user_id):
        rows.append([KeyboardButton(tx(data, "btn_admin"), style="primary")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True, input_field_placeholder="Choose an option…")


def admin_keyboard(data: dict[str, Any]) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(tx(data, "btn_add_style"), style="primary"), KeyboardButton(tx(data, "btn_import_json"), style="success")],
        [KeyboardButton(tx(data, "btn_export_json"), style="success"), KeyboardButton(tx(data, "btn_manage_styles"), style="primary")],
        [KeyboardButton(tx(data, "btn_manage_categories"), style="success"), KeyboardButton(tx(data, "btn_edit_texts"), style="primary")],
        [KeyboardButton(tx(data, "btn_stats"), style="success"), KeyboardButton(tx(data, "btn_back"), style="danger")],
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True)


def one_button_keyboard(label: str, style: str = "danger") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([[KeyboardButton(label, style=style)]], resize_keyboard=True)


def category_title(category: dict[str, Any]) -> str:
    return str(category.get("title", "Untitled Category"))


def mode_matches(style: dict[str, Any], mode: str) -> bool:
    style_mode = str(style.get("mode", "both"))
    if mode in ("name", "bulk"):
        return style_mode in ("name", "both")
    return style_mode in ("bio", "both")


def get_category_styles(data: dict[str, Any], category_id: str, mode: str | None = None) -> list[dict[str, Any]]:
    styles = []
    for sid, raw in data.get("styles", {}).items():
        if raw.get("category_id") != category_id or not raw.get("enabled", True):
            continue
        style = dict(raw)
        style["id"] = sid
        if mode and not mode_matches(style, mode):
            continue
        styles.append(style)
    return sorted(styles, key=lambda item: (int(item.get("order", 9999)), str(item.get("name", "")).casefold()))


def sorted_categories(data: dict[str, Any], mode: str | None = None, only_with_styles: bool = False) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for cid, raw in data.get("categories", {}).items():
        if not raw.get("enabled", True):
            continue
        cat = dict(raw)
        cat["id"] = cid
        if only_with_styles and not get_category_styles(data, cid, mode):
            continue
        out.append(cat)
    return sorted(out, key=lambda item: (int(item.get("order", 9999)), category_title(item).casefold()))


def category_button_label(data: dict[str, Any], category: dict[str, Any], mode: str) -> str:
    count = len(get_category_styles(data, category["id"], mode))
    return tx(data, "category_button_template", category=category_title(category), count=str(count))


def keyboard_rows(items: list[str], width: int = 2) -> list[list[str]]:
    return [items[i:i + width] for i in range(0, len(items), width)]


def make_category_keyboard(data: dict[str, Any], mode: str, page: int = 0) -> ReplyKeyboardMarkup:
    cats = sorted_categories(data, mode, only_with_styles=True)
    per_page = 6
    max_page = max(0, (len(cats) - 1) // per_page)
    page = max(0, min(page, max_page))
    chunk = cats[page * per_page:(page + 1) * per_page]
    rows = [[KeyboardButton(category_button_label(data, cat, mode), style=("primary" if i % 2 == 0 else "success"))] for i, cat in enumerate(chunk)]
    nav: list[str] = []
    if page > 0:
        nav.append(tx(data, "btn_cat_prev"))
    if page < max_page:
        nav.append(tx(data, "btn_cat_next"))
    if nav:
        rows.append([KeyboardButton(label, style="primary") for label in nav])
    rows.append([KeyboardButton(tx(data, "btn_new_name"), style="success"), KeyboardButton(tx(data, "btn_main_menu"), style="danger")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True)


def apply_style(style: dict[str, Any], value: str) -> str:
    transform = str(style.get("transform", "none"))
    custom_map = style.get("mapping")
    mapping = custom_map if isinstance(custom_map, dict) and custom_map else FONT_MAPS.get(transform, {})
    converted = "".join(str(mapping.get(char, char)) for char in value)
    template = str(style.get("template", "{name}"))
    if not any(token in template for token in ("{name}", "{text}", "{input}")):
        template = "{name}"
    result = template.replace("{name}", converted).replace("{text}", converted).replace("{input}", converted)
    return result


def current_labels(data: dict[str, Any]) -> dict[str, str]:
    return {key: tx(data, key) for key in DEFAULT_TEXTS}


def register_user(data: dict[str, Any], update: Update) -> bool:
    user = update.effective_user
    if not user:
        return False
    uid = str(user.id)
    existed = uid in data.get("users", {})
    entry = data.setdefault("users", {}).get(uid, {})
    entry.update({
        "first_name": (user.first_name or "")[:80],
        "username": (user.username or "")[:64],
        "last_seen": now_iso(),
    })
    entry.setdefault("first_seen", now_iso())
    data["users"][uid] = entry
    if not existed:
        STORE.save(data)
    return not existed


def style_count(data: dict[str, Any]) -> int:
    return sum(1 for style in data.get("styles", {}).values() if style.get("enabled", True))


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ----------------------------- User interface ----------------------------
async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict[str, Any], intro: bool = True) -> None:
    if not update.effective_message or not update.effective_user:
        return
    context.user_data.clear()
    text = tx(data, "welcome") + "\n\n" + tx(data, "action_prompt") if intro else tx(data, "action_prompt")
    await update.effective_message.reply_text(text, reply_markup=user_keyboard(data, update.effective_user.id))


async def ask_for_input(update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict[str, Any], mode: str) -> None:
    context.user_data["mode"] = mode
    context.user_data["flow"] = "await_user_input"
    prompt_key = {"name": "ask_name", "bio": "ask_bio", "bulk": "ask_bulk"}[mode]
    await update.effective_message.reply_text(tx(data, prompt_key), reply_markup=ReplyKeyboardMarkup(
        [[KeyboardButton(tx(data, "btn_cancel"), style="danger")], [KeyboardButton(tx(data, "btn_main_menu"), style="primary")]], resize_keyboard=True
    ))


async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict[str, Any], page: int = 0, *, message_obj=None) -> None:
    mode = context.user_data.get("mode", "name")
    vals = context.user_data.get("input_values", [])
    display_input = "\n".join(vals)
    cats = sorted_categories(data, mode, only_with_styles=True)
    if not cats:
        if message_obj:
            await message_obj.reply_text(tx(data, "empty_categories"), reply_markup=user_keyboard(data, update.effective_user.id))
        else:
            await update.effective_message.reply_text(tx(data, "empty_categories"), reply_markup=user_keyboard(data, update.effective_user.id))
        return
    per_page = 6
    max_page = max(0, (len(cats) - 1) // per_page)
    page = max(0, min(page, max_page))
    context.user_data["category_page"] = page
    keyboard = make_category_keyboard(data, mode, page)
    prompt = tx(data, "category_intro", input=display_input[:500])
    target = message_obj or update.effective_message
    await target.reply_text(prompt, reply_markup=keyboard)


async def show_styles(update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict[str, Any], page: int = 0, *, message_obj=None, edit_existing: bool = False) -> None:
    category_id = context.user_data.get("selected_category_id")
    mode = context.user_data.get("mode", "name")
    inputs = context.user_data.get("input_values", [])
    if not category_id:
        return
    styles = get_category_styles(data, category_id, mode)
    if not styles:
        target = message_obj or update.effective_message
        await target.reply_text(tx(data, "empty_styles"), reply_markup=make_category_keyboard(data, mode, context.user_data.get("category_page", 0)))
        return
    per_page = 6
    max_page = max(0, (len(styles) - 1) // per_page)
    page = max(0, min(page, max_page))
    context.user_data["style_page"] = page
    chunk = styles[page * per_page:(page + 1) * per_page]
    category = data.get("categories", {}).get(category_id, {})
    heading = tx(data, "style_heading", category=category_title(category).upper()) + "\n"
    heading += tx(data, "style_page_info", page=str(page + 1), pages=str(max_page + 1), count=str(len(styles))) + "\n"
    heading += tx(data, "style_divider") + "\n"
    lines: list[str] = []
    inline_rows: list[list[InlineKeyboardButton]] = []
    for offset, style in enumerate(chunk, start=page * per_page + 1):
        outputs = [apply_style(style, v) for v in inputs]
        full_result = "\n".join(outputs)
        display_result = full_result if len(full_result) <= 440 else full_result[:437] + "…"
        lines.append(f"{offset}. {style.get('name', 'Untitled Style')}\n{display_result}")
        if len(full_result) <= 256:
            inline_rows.append([InlineKeyboardButton(
                text=f"{tx(data, 'btn_copy_prefix')}{offset}",
                copy_text=CopyTextButton(text=full_result), style="primary",
            )])
        else:
            inline_rows.append([InlineKeyboardButton(
                text=f"📄 Full #{offset}", callback_data=f"full:{style['id']}", style="primary"
            )])
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(tx(data, "btn_style_prev"), callback_data=f"results:{page-1}", style="primary"))
    if page < max_page:
        nav.append(InlineKeyboardButton(tx(data, "btn_style_next"), callback_data=f"results:{page+1}", style="primary"))
    if nav:
        inline_rows.append(nav)
    inline_rows.append([
        InlineKeyboardButton(tx(data, "btn_collections"), callback_data="results:categories", style="success"),
        InlineKeyboardButton(tx(data, "btn_results_home"), callback_data="results:home", style="danger"),
    ])
    text = heading + "\n\n".join(lines)
    target = message_obj or update.effective_message
    markup = InlineKeyboardMarkup(inline_rows)
    if edit_existing and message_obj is not None:
        try:
            await message_obj.edit_text(text[:4090], reply_markup=markup)
            return
        except Exception as exc:
            logger.debug("Could not edit results page; sending a new message: %s", exc)
    await target.reply_text(text[:4090], reply_markup=markup)


# ------------------------------- Admin UI ---------------------------------
def admin_root_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Category", callback_data="cat:add")],
        [InlineKeyboardButton("📚 Browse Categories", callback_data="cat:list:0")],
    ])


def styles_list_markup(data: dict[str, Any], page: int = 0) -> InlineKeyboardMarkup:
    all_styles = sorted(
        [(sid, s) for sid, s in data.get("styles", {}).items()],
        key=lambda it: (int(it[1].get("order", 9999)), str(it[1].get("name", "")).casefold()),
    )
    per_page = 8
    max_page = max(0, (len(all_styles) - 1) // per_page)
    page = max(0, min(page, max_page))
    chunk = all_styles[page * per_page:(page + 1) * per_page]
    rows: list[list[InlineKeyboardButton]] = []
    for sid, style in chunk:
        status = "✅" if style.get("enabled", True) else "⏸"
        name = str(style.get("name", "Unnamed"))[:34]
        rows.append([InlineKeyboardButton(f"{status} {name} · {sid[-4:]}", callback_data=f"style:item:{sid}")])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"style:list:{page-1}"))
    if page < max_page:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"style:list:{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(tx(data, "btn_add_style"), callback_data="style:add", style="primary"), InlineKeyboardButton("↩️ Admin Menu", callback_data="admin:root", style="danger")])
    return InlineKeyboardMarkup(rows)


def categories_list_markup(data: dict[str, Any], page: int = 0) -> InlineKeyboardMarkup:
    cats = sorted_categories(data, mode=None, only_with_styles=False)
    # Include disabled categories in admin listing.
    all_cats = [(cid, dict(cat, id=cid)) for cid, cat in data.get("categories", {}).items()]
    all_cats.sort(key=lambda it: (int(it[1].get("order", 9999)), category_title(it[1]).casefold()))
    per_page = 8
    max_page = max(0, (len(all_cats) - 1) // per_page)
    page = max(0, min(page, max_page))
    chunk = all_cats[page * per_page:(page + 1) * per_page]
    rows: list[list[InlineKeyboardButton]] = []
    for cid, cat in chunk:
        status = "✅" if cat.get("enabled", True) else "⏸"
        title = category_title(cat)[:38]
        rows.append([InlineKeyboardButton(f"{status} {title}", callback_data=f"cat:item:{cid}")])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"cat:list:{page-1}"))
    if page < max_page:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"cat:list:{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(tx(data, "btn_add_category"), callback_data="cat:add", style="success"), InlineKeyboardButton("↩️ Admin Menu", callback_data="admin:root", style="danger")])
    return InlineKeyboardMarkup(rows)


def ui_texts_markup() -> InlineKeyboardMarkup:
    keys = list(TEXT_LABELS.items())
    rows: list[list[InlineKeyboardButton]] = []
    for start in range(0, len(keys), 2):
        row = [InlineKeyboardButton(label[:32], callback_data=f"text:edit:{key}") for key, label in keys[start:start + 2]]
        rows.append(row)
    rows.append([InlineKeyboardButton("↩️ Admin Menu", callback_data="admin:root")])
    return InlineKeyboardMarkup(rows)


def categories_for_add_style(data: dict[str, Any]) -> InlineKeyboardMarkup:
    cats = sorted_categories(data)
    rows = [[InlineKeyboardButton(category_title(cat)[:48], callback_data=f"addstyle:cat:{cat['id']}")] for cat in cats]
    rows.append([InlineKeyboardButton("➕ Create Category", callback_data="cat:add")])
    rows.append([InlineKeyboardButton("✖️ Cancel", callback_data="admin:root")])
    return InlineKeyboardMarkup(rows)


def transforms_markup(prefix: str, style_id: str | None = None) -> InlineKeyboardMarkup:
    keys = list(TRANSFORM_LABELS.items())
    rows: list[list[InlineKeyboardButton]] = []
    for start in range(0, len(keys), 2):
        row = []
        for key, label in keys[start:start + 2]:
            if prefix == "addstyle":
                cb = f"addstyle:transform:{key}"
            else:
                cb = f"style:transform:{style_id}:{key}"
            row.append(InlineKeyboardButton(label[:32], callback_data=cb))
        rows.append(row)
    rows.append([InlineKeyboardButton("✖️ Cancel", callback_data="admin:root")])
    return InlineKeyboardMarkup(rows)


def style_detail_markup(style_id: str, page: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Edit Name", callback_data=f"style:editname:{style_id}"), InlineKeyboardButton("🧩 Edit Template", callback_data=f"style:edittemplate:{style_id}")],
        [InlineKeyboardButton("🎨 Change Font", callback_data=f"style:choosefont:{style_id}"), InlineKeyboardButton("🗂 Change Category", callback_data=f"style:choosecat:{style_id}")],
        [InlineKeyboardButton("🔛 Enable / Disable", callback_data=f"style:toggle:{style_id}")],
        [InlineKeyboardButton("🗑 Delete", callback_data=f"style:delete:{style_id}"), InlineKeyboardButton("⬅️ Styles", callback_data=f"style:list:{page}")],
    ])


def category_detail_markup(category_id: str, page: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Rename", callback_data=f"cat:rename:{category_id}"), InlineKeyboardButton("🔛 Enable / Disable", callback_data=f"cat:toggle:{category_id}")],
        [InlineKeyboardButton("🗑 Delete Category + Its Styles", callback_data=f"cat:delete:{category_id}")],
        [InlineKeyboardButton("⬅️ Categories", callback_data=f"cat:list:{page}")],
    ])


async def send_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict[str, Any]) -> None:
    if not update.effective_user or not is_admin(update.effective_user.id) or not ensure_private(update):
        if update.effective_message:
            await update.effective_message.reply_text("⛔ This panel is private.")
        return
    context.user_data.pop("flow", None)
    body = (
        tx(data, "admin_title") + "\n" +
        "━━━━━━━━━━━━━━━━━━\n" +
        f"📚 Categories: {len(data.get('categories', {}))}\n"
        f"✨ Enabled styles: {style_count(data)}\n"
        f"👥 Users: {len(data.get('users', {}))}\n\n" +
        tx(data, "admin_intro")
    )
    await update.effective_message.reply_text(body, reply_markup=admin_keyboard(data))


# ---------------------------- Import / export ----------------------------
def sanitize_category(raw: dict[str, Any], old: dict[str, Any] | None = None) -> dict[str, Any]:
    title = str(raw.get("title", (old or {}).get("title", ""))).strip()
    if not title or len(title) > 70:
        raise ValueError("Every category needs a title (1–70 characters).")
    return {
        "title": title,
        "enabled": bool(raw.get("enabled", (old or {}).get("enabled", True))),
        "order": int(raw.get("order", (old or {}).get("order", 9999))),
    }


def sanitize_style(raw: dict[str, Any], category_ids: set[str], old: dict[str, Any] | None = None) -> dict[str, Any]:
    name = str(raw.get("name", (old or {}).get("name", ""))).strip()
    template = str(raw.get("template", (old or {}).get("template", "{name}")))
    category_id = str(raw.get("category_id", (old or {}).get("category_id", "")))
    mode = str(raw.get("mode", (old or {}).get("mode", "both"))).lower()
    transform = str(raw.get("transform", (old or {}).get("transform", "none"))).lower()
    mapping = raw.get("mapping", (old or {}).get("mapping", {}))
    if not name or len(name) > 70:
        raise ValueError("Every style needs a name (1–70 characters).")
    if len(template) > 200:
        raise ValueError(f"Template for '{name}' is longer than 200 characters.")
    if not any(token in template for token in ("{name}", "{text}", "{input}")):
        raise ValueError(f"Template for '{name}' must contain {{name}}, {{text}}, or {{input}}.")
    if category_id not in category_ids:
        raise ValueError(f"Style '{name}' refers to missing category_id '{category_id}'.")
    if mode not in ("name", "bio", "both"):
        raise ValueError(f"Invalid mode for '{name}'. Use name, bio, or both.")
    if transform not in TRANSFORM_LABELS:
        transform = "none"
    if not isinstance(mapping, dict):
        mapping = {}
    mapping = {str(k): str(v) for k, v in mapping.items() if len(str(k)) == 1 and len(str(v)) <= 12}
    return {
        "name": name,
        "category_id": category_id,
        "template": template,
        "transform": transform,
        "mapping": mapping,
        "mode": mode,
        "enabled": bool(raw.get("enabled", (old or {}).get("enabled", True))),
        "order": int(raw.get("order", (old or {}).get("order", 9999))),
    }


def apply_json_pack(current: dict[str, Any], pack: dict[str, Any], import_mode: str) -> tuple[dict[str, Any], int, int]:
    if not isinstance(pack, dict):
        raise ValueError("JSON root must be an object.")
    if import_mode not in ("merge", "replace"):
        raise ValueError("Import mode must be merge or replace.")
    cats = pack.get("categories", [])
    styles = pack.get("styles", [])
    texts = pack.get("texts", {})
    if not isinstance(cats, list) or not isinstance(styles, list) or not isinstance(texts, dict):
        raise ValueError("categories/styles must be arrays and texts must be an object.")
    if len(cats) > 500 or len(styles) > 5000:
        raise ValueError("This pack is too large (limit: 500 categories and 5000 styles).")
    result = copy.deepcopy(current)
    if import_mode == "replace":
        result["categories"] = {}
        result["styles"] = {}
    cat_count = 0
    for raw in cats:
        if not isinstance(raw, dict):
            raise ValueError("Each category must be an object.")
        cid = str(raw.get("id") or make_id("cat"))
        old = result["categories"].get(cid)
        result["categories"][cid] = sanitize_category(raw, old)
        cat_count += 1
    category_ids = set(result["categories"].keys())
    style_count_added = 0
    for raw in styles:
        if not isinstance(raw, dict):
            raise ValueError("Each style must be an object.")
        sid = str(raw.get("id") or make_id("style"))
        old = result["styles"].get(sid)
        result["styles"][sid] = sanitize_style(raw, category_ids, old)
        style_count_added += 1
    allowed_texts = set(DEFAULT_TEXTS.keys())
    for key, val in texts.items():
        if key in allowed_texts and isinstance(val, str) and len(val) <= 3500:
            result["texts"][key] = val
    STORE.save(result)
    return result, cat_count, style_count_added


# ----------------------------- Core handlers -----------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = STORE.load()
    register_user(data, update)
    await send_main_menu(update, context, data, intro=True)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = STORE.load()
    if update.effective_message:
        await update.effective_message.reply_text(tx(data, "help"), reply_markup=user_keyboard(data, update.effective_user.id if update.effective_user else 0))


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = STORE.load()
    if not update.effective_user or not is_admin(update.effective_user.id):
        if update.effective_message:
            await update.effective_message.reply_text("⛔ এই Admin Panel শুধু অনুমোদিত Admin-দের জন্য।")
        return
    await send_admin_panel(update, context, data)


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    data = STORE.load()
    if update.effective_message and update.effective_user:
        await update.effective_message.reply_text("Cancelled.", reply_markup=user_keyboard(data, update.effective_user.id))


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    if not message or not user or not message.text:
        return
    text = message.text.strip()
    data = STORE.load()
    register_user(data, update)

    if text in (tx(data, "btn_cancel"), "/cancel"):
        context.user_data.clear()
        await message.reply_text("Cancelled.", reply_markup=user_keyboard(data, user.id))
        return
    if text == tx(data, "btn_main_menu"):
        await send_main_menu(update, context, data, intro=True)
        return
    if text == tx(data, "btn_admin"):
        await send_admin_panel(update, context, data)
        return

    flow = context.user_data.get("flow")
    # ---------- User input flow ----------
    if flow == "await_user_input":
        mode = context.user_data.get("mode", "name")
        if mode == "bulk":
            values = [line.strip() for line in re.split(r"[\n,]+", text) if line.strip()]
            if len(values) > 8:
                await message.reply_text("একবারে সর্বোচ্চ ৮টি নাম পাঠাও। আবার চেষ্টা করো।")
                return
            if not values or any(len(v) > 45 for v in values):
                await message.reply_text("প্রতিটি নাম ১–৪৫ অক্ষরের মধ্যে রাখো।")
                return
        else:
            values = [text]
            if len(text) > 120:
                await message.reply_text("লেখাটি অনেক বড়। ১২০ অক্ষরের মধ্যে পাঠাও।")
                return
        context.user_data["input_values"] = values
        context.user_data["flow"] = "choose_category"
        await show_categories(update, context, data, page=0)
        return

    # ---------- Admin text-input flows ----------
    if (not is_admin(user.id) or not ensure_private(update)) and str(flow or "").startswith("admin_"):
        # Drop only admin-specific states; normal users still need their category-selection flow.
        context.user_data.pop("flow", None)

    if is_admin(user.id) and ensure_private(update):
        if flow == "admin_edit_category_title":
            cid = context.user_data.get("edit_category_id")
            if cid not in data.get("categories", {}):
                context.user_data.pop("flow", None)
                await message.reply_text("Category পাওয়া যায়নি।")
                return
            if not text or len(text) > 70:
                await message.reply_text("Category name ১–৭০ অক্ষরের মধ্যে রাখো।")
                return
            data["categories"][cid]["title"] = text
            STORE.save(data)
            context.user_data.pop("flow", None)
            context.user_data.pop("edit_category_id", None)
            await message.reply_text("✅ Category renamed.", reply_markup=admin_keyboard(data))
            return
        if flow == "admin_add_name":
            if len(text) > 70:
                await message.reply_text("Style name ৭০ অক্ষরের মধ্যে রাখো।")
                return
            context.user_data["draft_style"] = {"name": text}
            cats = sorted_categories(data)
            if not cats:
                await message.reply_text("আগে অন্তত একটি Category তৈরি করো: Admin Panel → Manage Categories → Add Category.", reply_markup=admin_keyboard(data))
                context.user_data.pop("flow", None)
                return
            context.user_data["flow"] = "admin_add_category"
            await message.reply_text("এই Style কোন Collection-এ থাকবে?", reply_markup=ReplyKeyboardRemove())
            await message.reply_text("Collection বেছে নাও:", reply_markup=categories_for_add_style(data))
            return
        if flow == "admin_add_template":
            if len(text) > 200 or not any(token in text for token in ("{name}", "{text}", "{input}")):
                await message.reply_text("Template-এ {name} বা {text} থাকতে হবে; সর্বোচ্চ ২০০ অক্ষর।\nউদাহরণ: ♡ {name} 𓆩♡𓆪")
                return
            draft = context.user_data.get("draft_style", {})
            if not draft.get("category_id"):
                await message.reply_text("Category পাওয়া যায়নি। আবার Add Style শুরু করো।")
                context.user_data.pop("flow", None)
                return
            sid = make_id("style")
            data["styles"][sid] = {
                "name": draft["name"],
                "category_id": draft["category_id"],
                "template": text,
                "transform": draft.get("transform", "none"),
                "mapping": {},
                "mode": draft.get("mode", "both"),
                "enabled": True,
                "order": len(data["styles"]) + 1,
            }
            STORE.save(data)
            context.user_data.pop("flow", None)
            context.user_data.pop("draft_style", None)
            await message.reply_text(
                f"✅ Style যোগ হয়েছে!\n\nName: {data['styles'][sid]['name']}\nTemplate: {text}\nFont: {TRANSFORM_LABELS.get(data['styles'][sid]['transform'], 'Plain')}\nID: {sid}",
                reply_markup=admin_keyboard(data),
            )
            return
        if flow == "admin_new_category_title":
            if not text or len(text) > 70:
                await message.reply_text("Category name ১–৭০ অক্ষরের মধ্যে রাখো।")
                return
            cid = make_id("cat")
            data["categories"][cid] = {"title": text, "enabled": True, "order": len(data["categories"]) + 1}
            STORE.save(data)
            context.user_data.pop("flow", None)
            await message.reply_text(f"✅ Category যোগ হয়েছে: {text}", reply_markup=admin_keyboard(data))
            return
        if flow == "admin_edit_text_value":
            key = context.user_data.get("edit_text_key")
            if key not in DEFAULT_TEXTS:
                context.user_data.pop("flow", None)
                await message.reply_text("Text key পাওয়া যায়নি।")
                return
            if len(text) > 3500:
                await message.reply_text("Text ৩৫০০ অক্ষরের মধ্যে রাখো।")
                return
            data["texts"][key] = text
            STORE.save(data)
            context.user_data.pop("flow", None)
            context.user_data.pop("edit_text_key", None)
            await message.reply_text(f"✅ Updated: {TEXT_LABELS.get(key, key)}", reply_markup=admin_keyboard(data))
            return
        if flow == "admin_edit_style_field":
            sid = context.user_data.get("edit_style_id")
            field = context.user_data.get("edit_style_field")
            style = data.get("styles", {}).get(sid)
            if not style:
                context.user_data.pop("flow", None)
                await message.reply_text("Style পাওয়া যায়নি।")
                return
            if field == "name":
                if not text or len(text) > 70:
                    await message.reply_text("Style name ১–৭০ অক্ষরের মধ্যে রাখো।")
                    return
                style["name"] = text
            elif field == "template":
                if len(text) > 200 or not any(token in text for token in ("{name}", "{text}", "{input}")):
                    await message.reply_text("Template-এ {name} বা {text} থাকতে হবে; সর্বোচ্চ ২০০ অক্ষর।")
                    return
                style["template"] = text
            elif field == "category":
                matches = [cid for cid, cat in data["categories"].items() if category_title(cat) == text]
                if not matches:
                    await message.reply_text("ঠিক Category নামটি বেছে নাও।")
                    return
                style["category_id"] = matches[0]
            STORE.save(data)
            context.user_data.pop("flow", None)
            await message.reply_text("✅ Style আপডেট হয়েছে।", reply_markup=admin_keyboard(data))
            return
        if flow == "admin_wait_json":
            await message.reply_text("📥 JSON ফাইলটি document হিসেবে পাঠাও। শুধু JSON-এর text paste করলেও হবে না—ফাইল পাঠানোই ভালো।")
            return

    # ---------- Menu routing ----------
    if text == tx(data, "btn_name"):
        await ask_for_input(update, context, data, "name")
        return
    if text == tx(data, "btn_bio"):
        await ask_for_input(update, context, data, "bio")
        return
    if text == tx(data, "btn_bulk"):
        await ask_for_input(update, context, data, "bulk")
        return
    if text == tx(data, "btn_help") or text == "/help":
        await message.reply_text(tx(data, "help"), reply_markup=user_keyboard(data, user.id))
        return
    if is_admin(user.id) and ensure_private(update):
        if text == tx(data, "btn_add_style"):
            context.user_data["flow"] = "admin_add_name"
            context.user_data["draft_style"] = {}
            await message.reply_text("নতুন Style-এর display name পাঠাও।\nউদাহরণ: Elegant Heart", reply_markup=one_button_keyboard(tx(data, "btn_cancel")))
            return
        if text == tx(data, "btn_import_json"):
            await message.reply_text("Import mode বেছে নাও। Merge পুরোনো Style রেখে যোগ/আপডেট করবে; Replace All বর্তমান categories/styles বদলে দেবে।", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Merge", callback_data="import:merge"), InlineKeyboardButton("♻️ Replace All", callback_data="import:replace")],
                [InlineKeyboardButton("✖️ Cancel", callback_data="admin:root")],
            ]))
            return
        if text == tx(data, "btn_export_json"):
            payload = {
                "schema_version": 1,
                "categories": [dict(item, id=cid) for cid, item in data.get("categories", {}).items()],
                "styles": [dict(item, id=sid) for sid, item in data.get("styles", {}).items()],
                "texts": data.get("texts", {}),
            }
            output = BytesIO(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))
            output.name = "stylish_name_maker_backup.json"
            await message.reply_document(InputFile(output, filename=output.name), caption="📤 Current styles, categories and UI text backup.")
            return
        if text == tx(data, "btn_manage_styles"):
            context.user_data["style_list_page"] = 0
            await message.reply_text("🧩 STYLE MANAGER\nএকটি Style বেছে নিয়ে Edit, Change Font, Disable বা Delete করতে পারো.", reply_markup=styles_list_markup(data, 0))
            return
        if text == tx(data, "btn_manage_categories"):
            await message.reply_text("🗂 CATEGORY MANAGER\nCategory যোগ, rename, enable/disable বা delete করো.", reply_markup=categories_list_markup(data, 0))
            return
        if text == tx(data, "btn_edit_texts"):
            await message.reply_text("📝 যে UI Text বা Button Label পরিবর্তন করতে চাও, সেটি বেছে নাও.", reply_markup=ui_texts_markup())
            return
        if text == tx(data, "btn_stats"):
            await message.reply_text(
                "✦ BOT STATISTICS ✦\n\n"
                f"👥 Users: {len(data.get('users', {}))}\n"
                f"🗂 Categories: {len(data.get('categories', {}))}\n"
                f"✨ Total Styles: {len(data.get('styles', {}))}\n"
                f"✅ Enabled Styles: {style_count(data)}\n"
                f"🎯 Generated sessions: {data.get('usage', {}).get('generated', 0)}\n"
                f"🚀 Bulk requests: {data.get('usage', {}).get('bulk_jobs', 0)}",
                reply_markup=admin_keyboard(data),
            )
            return
        if text == tx(data, "btn_back"):
            await send_main_menu(update, context, data, intro=True)
            return

    # Category selection / navigation is resolved using saved category data, not arbitrary command text.
    mode = context.user_data.get("mode")
    if context.user_data.get("flow") == "choose_category" and mode:
        if text == tx(data, "btn_cat_prev"):
            await show_categories(update, context, data, max(0, context.user_data.get("category_page", 0) - 1))
            return
        if text == tx(data, "btn_cat_next"):
            await show_categories(update, context, data, context.user_data.get("category_page", 0) + 1)
            return
        for cat in sorted_categories(data, mode, only_with_styles=True):
            if text == category_button_label(data, cat, mode) or text == category_title(cat) or text.startswith(category_title(cat) + " ("):
                context.user_data["selected_category_id"] = cat["id"]
                context.user_data["flow"] = "showing_styles"
                data.setdefault("usage", {}).setdefault("generated", 0)
                data["usage"]["generated"] = int(data["usage"]["generated"]) + 1
                if mode == "bulk":
                    data["usage"]["bulk_jobs"] = int(data["usage"].get("bulk_jobs", 0)) + 1
                STORE.save(data)
                await show_styles(update, context, data, page=0)
                return
    if text == tx(data, "btn_new_name"):
        await ask_for_input(update, context, data, context.user_data.get("mode", "name"))
        return

    if is_admin(user.id) and ensure_private(update):
        # Editing a style category via reply-keyboard selection.
        if context.user_data.get("flow") == "admin_edit_style_field" and context.user_data.get("edit_style_field") == "category":
            matches = [cid for cid, cat in data["categories"].items() if category_title(cat) == text]
            if matches:
                sid = context.user_data.get("edit_style_id")
                if sid in data["styles"]:
                    data["styles"][sid]["category_id"] = matches[0]
                    STORE.save(data)
                    context.user_data.pop("flow", None)
                    await message.reply_text("✅ Category পরিবর্তন হয়েছে।", reply_markup=admin_keyboard(data))
                    return

    await message.reply_text(tx(data, "action_prompt"), reply_markup=user_keyboard(data, user.id))


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    if not message or not user or not message.document:
        return
    data = STORE.load()
    if not is_admin(user.id) or not ensure_private(update):
        await message.reply_text("⛔ JSON import শুধু অনুমোদিত Admin-এর private chat-এ চালু।")
        return
    if context.user_data.get("flow") != "admin_wait_json":
        await message.reply_text("প্রথমে Admin Panel → Import JSON থেকে Merge বা Replace All বেছে নাও।", reply_markup=admin_keyboard(data))
        return
    filename = message.document.file_name or ""
    if not filename.lower().endswith(".json"):
        await message.reply_text("শুধু .json ফাইল পাঠাও।")
        return
    if message.document.file_size and message.document.file_size > 1_500_000:
        await message.reply_text("JSON ফাইল ১.৫ MB-এর কম হতে হবে।")
        return
    try:
        file = await message.document.get_file()
        raw = await file.download_as_bytearray()
        pack = json.loads(bytes(raw).decode("utf-8-sig"))
        new_data, cat_count, style_count_added = apply_json_pack(data, pack, context.user_data.get("import_mode", "merge"))
        context.user_data.pop("flow", None)
        context.user_data.pop("import_mode", None)
        await message.reply_text(
            "✅ JSON import complete!\n\n"
            f"🗂 Categories processed: {cat_count}\n"
            f"✨ Styles processed: {style_count_added}\n"
            f"📚 Total saved styles: {style_count(new_data)}\n\n"
            "পরবর্তী ব্যবহার থেকেই নতুন Style দেখা যাবে; redeploy লাগবে না।",
            reply_markup=admin_keyboard(new_data),
        )
    except Exception as exc:
        logger.warning("JSON import failed: %s", exc)
        await message.reply_text(f"❌ Import failed: {str(exc)[:500]}\nফাইলের format ও category_id মিলিয়ে আবার পাঠাও।")


# --------------------------- Callback handling ---------------------------
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return
    data = STORE.load()
    payload = query.data or ""
    if payload.startswith("admin:") or payload.startswith(("cat:", "style:", "text:", "addstyle:", "import:")):
        if not is_admin(user.id) or not ensure_private(update):
            await query.answer("Not authorized", show_alert=True)
            return
    await query.answer()

    if payload.startswith("full:"):
        sid = payload.split(":", 1)[1]
        style = data.get("styles", {}).get(sid)
        inputs = context.user_data.get("input_values", [])
        mode = context.user_data.get("mode", "name")
        if not style or not inputs or not mode_matches(style, mode):
            await query.message.reply_text("এই ফলাফলের session শেষ হয়েছে। আবার নাম দিয়ে শুরু করো।")
            return
        output = "\n".join(apply_style(style, value) for value in inputs)
        heading = f"✦ {style.get('name', 'Style')} ✦\n\n"
        await query.message.reply_text((heading + output)[:4090], reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Back to Styles", callback_data=f"results:{context.user_data.get('style_page', 0)}", style="primary")]
        ]))
        return

    if payload == "results:home":
        context.user_data.pop("flow", None)
        context.user_data.pop("mode", None)
        context.user_data.pop("input_values", None)
        await query.message.reply_text(tx(data, "welcome") + "\n\n" + tx(data, "action_prompt"), reply_markup=user_keyboard(data, user.id))
        return
    if payload == "results:categories":
        context.user_data["flow"] = "choose_category"
        await show_categories(update, context, data, context.user_data.get("category_page", 0), message_obj=query.message)
        return
    if payload.startswith("results:"):
        try:
            page = int(payload.split(":", 1)[1])
        except ValueError:
            page = 0
        await show_styles(update, context, data, page, message_obj=query.message, edit_existing=True)
        return

    # Admin panel entry point.
    if payload == "admin:root":
        context.user_data.pop("flow", None)
        context.user_data.pop("draft_style", None)
        await query.message.reply_text(
            tx(data, "admin_title") + "\n\n" +
            f"Categories: {len(data.get('categories', {}))}  •  Enabled Styles: {style_count(data)}  •  Users: {len(data.get('users', {}))}\n\n" + tx(data, "admin_intro"),
            reply_markup=admin_keyboard(data),
        )
        return

    # Imports.
    if payload in ("import:merge", "import:replace"):
        context.user_data["flow"] = "admin_wait_json"
        context.user_data["import_mode"] = payload.split(":")[1]
        if context.user_data["import_mode"] == "replace":
            warn = "⚠️ Replace All selected: the imported pack will replace current categories/styles. Send the JSON file to confirm."
        else:
            warn = "✅ Merge selected: matching IDs will update; new IDs will be added. Send the JSON file."
        await query.message.reply_text(warn, reply_markup=one_button_keyboard(tx(data, "btn_cancel")))
        return

    # Add style wizard.
    if payload == "style:add":
        context.user_data["flow"] = "admin_add_name"
        context.user_data["draft_style"] = {}
        await query.message.reply_text("নতুন Style-এর display name পাঠাও।\nউদাহরণ: Elegant Heart", reply_markup=one_button_keyboard(tx(data, "btn_cancel")))
        return
    if payload.startswith("addstyle:cat:"):
        cid = payload.split(":", 2)[2]
        if cid not in data.get("categories", {}):
            await query.message.reply_text("Category আর পাওয়া যাচ্ছে না। আবার চেষ্টা করো।")
            return
        draft = context.user_data.setdefault("draft_style", {})
        draft["category_id"] = cid
        context.user_data["flow"] = "admin_add_mode"
        await query.message.reply_text("এই Style কোথায় ব্যবহার হবে?", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Name", callback_data="addstyle:mode:name"), InlineKeyboardButton("Bio", callback_data="addstyle:mode:bio"), InlineKeyboardButton("Both", callback_data="addstyle:mode:both")],
            [InlineKeyboardButton("✖️ Cancel", callback_data="admin:root")],
        ]))
        return
    if payload.startswith("addstyle:mode:"):
        mode = payload.split(":")[2]
        if mode not in ("name", "bio", "both"):
            await query.message.reply_text("Invalid mode.")
            return
        context.user_data.setdefault("draft_style", {})["mode"] = mode
        context.user_data["flow"] = "admin_add_transform"
        await query.message.reply_text("Font transform বেছে নাও। পরে template-এ {name} দিয়ে নামের জায়গা বোঝাবে।", reply_markup=transforms_markup("addstyle"))
        return
    if payload.startswith("addstyle:transform:"):
        transform = payload.split(":", 2)[2]
        if transform not in TRANSFORM_LABELS:
            transform = "none"
        context.user_data.setdefault("draft_style", {})["transform"] = transform
        context.user_data["flow"] = "admin_add_template"
        await query.message.reply_text(
            "এখন Template পাঠাও।\n\n"
            "উদাহরণ: ♡ {name} ♡\n"
            "অথবা: ꧁༺ {name} ༻꧂\n"
            "শুধু Font Style হলে: {name}\n\n"
            "Placeholder অবশ্যই {name}, {text}, বা {input} হতে হবে।",
            reply_markup=one_button_keyboard(tx(data, "btn_cancel")),
        )
        return

    # Style manager.
    if payload.startswith("style:list:"):
        page = int(payload.split(":")[2])
        context.user_data["style_list_page"] = page
        await query.message.reply_text("🧩 STYLE MANAGER", reply_markup=styles_list_markup(data, page))
        return
    if payload.startswith("style:item:"):
        sid = payload.split(":", 2)[2]
        style = data.get("styles", {}).get(sid)
        if not style:
            await query.message.reply_text("Style not found.", reply_markup=styles_list_markup(data, 0))
            return
        cat = data.get("categories", {}).get(style.get("category_id"), {})
        sample = apply_style(style, "Jisan")
        body = (
            "✦ 𝗦𝗧𝗬𝗟𝗘 𝗗𝗘𝗧𝗔𝗜𝗟 ✦\n\n"
            f"Name: {style.get('name')}\nID: {sid}\n"
            f"Category: {category_title(cat)}\n"
            f"Mode: {style.get('mode', 'both')}\n"
            f"Font: {TRANSFORM_LABELS.get(style.get('transform', 'none'), 'Plain')}\n"
            f"Template: {style.get('template')}\n"
            f"Preview: {sample}\n"
            f"Status: {'Enabled' if style.get('enabled', True) else 'Disabled'}"
        )
        page = int(context.user_data.get("style_list_page", 0))
        context.user_data["selected_style_id"] = sid
        await query.message.reply_text(body[:3900], reply_markup=style_detail_markup(sid, page))
        return
    if payload.startswith("style:editname:") or payload.startswith("style:edittemplate:"):
        _, action, sid = payload.split(":", 2)
        if sid not in data.get("styles", {}):
            await query.message.reply_text("Style not found.")
            return
        field = "name" if action == "editname" else "template"
        context.user_data["flow"] = "admin_edit_style_field"
        context.user_data["edit_style_id"] = sid
        context.user_data["edit_style_field"] = field
        cur = data["styles"][sid].get(field, "")
        await query.message.reply_text(f"Current {field}: {cur}\n\nনতুন {field} পাঠাও; বাতিল করতে Cancel চাপো।", reply_markup=one_button_keyboard(tx(data, "btn_cancel")))
        return
    if payload.startswith("style:choosefont:"):
        sid = payload.split(":", 2)[2]
        await query.message.reply_text("নতুন font mapping বেছে নাও:", reply_markup=transforms_markup("edit", sid))
        return
    if payload.startswith("style:transform:"):
        _, _, sid, transform = payload.split(":", 3)
        if sid in data.get("styles", {}) and transform in TRANSFORM_LABELS:
            data["styles"][sid]["transform"] = transform
            STORE.save(data)
            await query.message.reply_text(f"✅ Font updated: {TRANSFORM_LABELS[transform]}", reply_markup=style_detail_markup(sid))
        return
    if payload.startswith("style:choosecat:"):
        sid = payload.split(":", 2)[2]
        if sid not in data.get("styles", {}):
            await query.message.reply_text("Style not found.")
            return
        context.user_data["flow"] = "admin_edit_style_field"
        context.user_data["edit_style_id"] = sid
        context.user_data["edit_style_field"] = "category"
        cats = sorted_categories(data)
        rows = [[InlineKeyboardButton(category_title(cat)[:48], callback_data=f"style:setcat:{sid}:{cat['id']}")] for cat in cats]
        rows.append([InlineKeyboardButton("✖️ Cancel", callback_data=f"style:item:{sid}")])
        await query.message.reply_text("নতুন Category বেছে নাও:", reply_markup=InlineKeyboardMarkup(rows))
        return
    if payload.startswith("style:setcat:"):
        _, _, sid, cid = payload.split(":", 3)
        if sid in data.get("styles", {}) and cid in data.get("categories", {}):
            data["styles"][sid]["category_id"] = cid
            STORE.save(data)
            context.user_data.pop("flow", None)
            await query.message.reply_text("✅ Category updated.", reply_markup=style_detail_markup(sid))
        return
    if payload.startswith("style:toggle:"):
        sid = payload.split(":", 2)[2]
        if sid in data.get("styles", {}):
            data["styles"][sid]["enabled"] = not data["styles"][sid].get("enabled", True)
            STORE.save(data)
            await query.message.reply_text("✅ Status updated.", reply_markup=style_detail_markup(sid))
        return
    if payload.startswith("style:delete:"):
        sid = payload.split(":", 2)[2]
        await query.message.reply_text("এই Style স্থায়ীভাবে Delete করবে?", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🗑 Yes, Delete", callback_data=f"style:confirmdelete:{sid}"), InlineKeyboardButton("Cancel", callback_data=f"style:item:{sid}")]
        ]))
        return
    if payload.startswith("style:confirmdelete:"):
        sid = payload.split(":", 2)[2]
        existed = data.get("styles", {}).pop(sid, None)
        if existed is not None:
            STORE.save(data)
        await query.message.reply_text("✅ Deleted." if existed is not None else "Style already removed.", reply_markup=styles_list_markup(data, 0))
        return

    # Category manager.
    if payload == "cat:add":
        context.user_data["flow"] = "admin_new_category_title"
        await query.message.reply_text("নতুন Category-এর নাম পাঠাও।\nউদাহরণ: 🌷 Cute & Symbolic", reply_markup=one_button_keyboard(tx(data, "btn_cancel")))
        return
    if payload.startswith("cat:list:"):
        page = int(payload.split(":")[2])
        await query.message.reply_text("🗂 CATEGORY MANAGER", reply_markup=categories_list_markup(data, page))
        return
    if payload.startswith("cat:item:"):
        cid = payload.split(":", 2)[2]
        cat = data.get("categories", {}).get(cid)
        if not cat:
            await query.message.reply_text("Category not found.", reply_markup=categories_list_markup(data, 0))
            return
        count = sum(1 for st in data.get("styles", {}).values() if st.get("category_id") == cid)
        await query.message.reply_text(
            f"✦ CATEGORY DETAIL ✦\n\nName: {category_title(cat)}\nID: {cid}\nStyles: {count}\nStatus: {'Enabled' if cat.get('enabled', True) else 'Disabled'}",
            reply_markup=category_detail_markup(cid),
        )
        return
    if payload.startswith("cat:rename:"):
        cid = payload.split(":", 2)[2]
        if cid not in data.get("categories", {}):
            await query.message.reply_text("Category not found.")
            return
        context.user_data["flow"] = "admin_edit_category_title"
        context.user_data["edit_category_id"] = cid
        await query.message.reply_text(f"Current: {category_title(data['categories'][cid])}\nনতুন নাম পাঠাও।", reply_markup=one_button_keyboard(tx(data, "btn_cancel")))
        return
    if payload.startswith("cat:toggle:"):
        cid = payload.split(":", 2)[2]
        if cid in data.get("categories", {}):
            data["categories"][cid]["enabled"] = not data["categories"][cid].get("enabled", True)
            STORE.save(data)
            await query.message.reply_text("✅ Category status updated.", reply_markup=category_detail_markup(cid))
        return
    if payload.startswith("cat:delete:"):
        cid = payload.split(":", 2)[2]
        await query.message.reply_text("এই Category-এর সব Style-সহ Delete হবে। নিশ্চিত?", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🗑 Delete Category + Styles", callback_data=f"cat:confirmdelete:{cid}")],
            [InlineKeyboardButton("Cancel", callback_data=f"cat:item:{cid}")],
        ]))
        return
    if payload.startswith("cat:confirmdelete:"):
        cid = payload.split(":", 2)[2]
        existed = data.get("categories", {}).pop(cid, None)
        remove_ids = [sid for sid, style in data.get("styles", {}).items() if style.get("category_id") == cid]
        for sid in remove_ids:
            data["styles"].pop(sid, None)
        STORE.save(data)
        await query.message.reply_text(f"✅ Deleted category and {len(remove_ids)} style(s)." if existed else "Category already removed.", reply_markup=categories_list_markup(data, 0))
        return

    # UI text manager.
    if payload.startswith("text:edit:"):
        key = payload.split(":", 2)[2]
        if key not in DEFAULT_TEXTS:
            await query.message.reply_text("Unknown text key.")
            return
        context.user_data["flow"] = "admin_edit_text_value"
        context.user_data["edit_text_key"] = key
        current = tx(data, key)
        await query.message.reply_text(
            f"📝 {TEXT_LABELS.get(key, key)}\n\nCurrent text:\n{current[:1500]}\n\nনতুন text পাঠাও। Placeholder যেমন {{input}} থাকলে অপরিবর্তিত রাখবে।",
            reply_markup=one_button_keyboard(tx(data, "btn_cancel")),
        )
        return


async def set_bot_commands(app: Application) -> None:
    await app.bot.set_my_commands([
        BotCommand("start", "Open the main menu"),
        BotCommand("help", "How to use the bot"),
        BotCommand("cancel", "Cancel the current action"),
    ])


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled bot error", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text("একটু সমস্যা হয়েছে। আবার চেষ্টা করো অথবা /start পাঠাও।")
        except Exception:
            pass


def main() -> None:
    if not BOT_TOKEN:
        raise SystemExit("Missing BOT_TOKEN. Add your Telegram bot token to the BOT_TOKEN environment variable.")
    app = Application.builder().token(BOT_TOKEN).post_init(set_bot_commands).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)
    logger.info("Starting Stylish Name Maker bot; admin IDs configured: %s", sorted(ADMIN_IDS))
    app.run_polling(drop_pending_updates=False, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
