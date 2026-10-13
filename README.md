# Stylish Name Maker — Premium Dynamic Edition

A Telegram bot built around the reference flow: Make My Name, BIO, Bulk Names, Help → choose a collection → browse paginated styles → one-tap copy for short results or open the full result for longer outputs. Reply-keyboard buttons use Telegram’s blue/green/red button styles where the client supports them. The separate starter pack has 100 styles across five non-gaming collections.

## What is configurable inside Telegram

Only the two Telegram IDs in `ADMIN_IDS` (default: `8223664417,8819766785`) can see and use the Admin Panel. Access is checked again for every admin callback/document, not just by hiding the button.

- Add styles through a guided form (name, category, mode, Unicode font transform, template).
- Import a JSON pack using **Merge** or **Replace All**.
- Export a backup JSON.
- Rename/enable/disable/delete categories.
- Edit style name/template/font/category, enable/disable, or delete.
- Change many user-facing texts and button labels.
- See basic user/style counts.

Style and category content is not hard-coded in the project; the separate `starter_styles.json` file is supplied beside the project ZIP and can be uploaded directly to the bot. Do not add that JSON pack to the deployment repository unless you specifically want it public.

## 1. Create the bot

1. Open Telegram and use `@BotFather` to create a bot.
2. Copy its token. Do not send the token in chat or commit it to GitHub.
3. Upload these project files to your GitHub repository, **but do not add secrets or `starter_styles.json`**.

## 2. Firebase Realtime Database (recommended for Render)

The local `data/bot_data.json` mode is for testing only. Render may replace local files during redeploy/restart; configure Firebase to keep style edits after restarts.

1. Open the Firebase project you want this bot to use.
2. Create/enable a **Realtime Database** and copy its database URL.
3. In Project Settings → Service accounts, generate a private key for a server-side service account. Keep it private.
4. In the Render service's Environment settings, set:
   - `BOT_TOKEN` = the BotFather token
   - `ADMIN_IDS` = `8223664417,8819766785`
   - `FIREBASE_DATABASE_URL` = the Realtime Database URL
   - `FIREBASE_CREDENTIALS_JSON` = the **entire service-account JSON contents** as one environment-variable value
5. Never upload the service-account JSON to GitHub or send it to anyone.

The bot stores its data under `/stylish_name_maker`, so it does not overwrite other top-level paths in the same Realtime Database. Review Firebase database rules and restrict client-side public writes; the service-account credential belongs only in Render's private environment.

## 3. Run on Render

Use a **Background Worker** for Telegram long polling, with build command `pip install -r requirements.txt` and start command `python bot.py`. Select Python 3.11.9 (the included `.python-version` is a hint). Add the environment variables above. Keep one active polling instance for this bot token to avoid competing pollers.

## 4. Load the starter style pack

After deploying and opening the bot as one of the configured admins:

1. Tap **🛠 Admin Panel**.
2. Tap **📥 Import JSON**.
3. Select **➕ Merge** for first-time import.
4. Send the separate `starter_styles.json` file as a Telegram document.

You can later upload your own JSON pack the same way. Style changes are read from the database on the next interaction; no redeploy is needed for data-only changes.

## JSON pack format (version 1)

```json
{
  "schema_version": 1,
  "categories": [
    {"id": "cat_aesthetic", "title": "✨ Aesthetic Art Styles", "enabled": true, "order": 1}
  ],
  "styles": [
    {
      "id": "style_script_01",
      "name": "Elegant Script",
      "category_id": "cat_aesthetic",
      "template": "{name}",
      "transform": "script",
      "mode": "both",
      "enabled": true,
      "order": 1
    },
    {
      "id": "style_heart_01",
      "name": "Soft Heart",
      "category_id": "cat_aesthetic",
      "template": "♡ {name} 𓆩♡𓆪",
      "transform": "none",
      "mode": "both",
      "enabled": true,
      "order": 2
    }
  ],
  "texts": {
    "welcome": "Your editable welcome text"
  }
}
```

Supported `transform` values: `none`, `bold`, `italic`, `bold_italic`, `script`, `script_bold`, `fraktur`, `double_struck`, `sans`, `sans_bold`, `sans_italic`, `monospace`, `small_caps`, `fullwidth`.

To add a custom per-character font mapping, include a `mapping` object, for example `{"mapping":{"A":"ᗩ","B":"ᗷ"}}`. Characters not listed are preserved. Template placeholders: `{name}`, `{text}`, `{input}`.

Merge mode adds/updates items by ID; Replace All replaces categories and styles from the imported pack. Always export a backup before using Replace All.

## Important limits

- This is a Telegram bot, so the UI is made from Telegram messages and keyboards—not a separate full-screen app UI.
- Manual style templates and JSON packs can be changed without redeploy; new programming logic requires a code update.
- Built-in font transforms support Latin characters/digits; Bengali characters remain unchanged unless you provide a custom mapping.
- The bot source and data/template logic have been syntax-checked and tested locally with mocked Telegram objects. It has not been live-tested against your BotFather token/Firebase project. Configure the environment variables before deploying.
