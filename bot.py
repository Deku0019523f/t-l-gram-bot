import os
import logging
import tempfile
import requests
from telegram import Update, InputFile, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
VT_API_KEY = os.getenv("VT_API_KEY")
CHANNEL_USERNAME = "@up78ma0Ev642YWM0"
ADMIN_ID = 1299831974

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_subscription(context, user_id):
        await ask_to_subscribe(update)
        return
    await update.message.reply_text("Bienvenue sur le bot de @deku225 vous pouvez m'envoyer vos liens et apk suspect pour les analyser")

async def check_subscription(context, user_id):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

async def ask_to_subscribe(update):
    keyboard = [[InlineKeyboardButton("S'abonner au canal", url="https://t.me/+up78ma0Ev642YWM0")]]
    await update.message.reply_text("Vous devez vous abonner au canal pour utiliser ce bot.", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_subscription(context, user_id):
        await ask_to_subscribe(update)
        return

    document = update.message.document
    if not document.file_name.endswith(".apk"):
        await update.message.reply_text("Le fichier n'est pas un APK.")
        return

    file = await context.bot.get_file(document.file_id)
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        await file.download_to_drive(tmp.name)
        result = scan_file(tmp.name)
        await update.message.reply_text(result)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_subscription(context, user_id):
        await ask_to_subscribe(update)
        return

    url = update.message.text.strip()
    result = scan_url(url)
    await update.message.reply_text(result)

def scan_file(filepath):
    url = "https://www.virustotal.com/api/v3/files"
    headers = {"x-apikey": VT_API_KEY}
    with open(filepath, "rb") as f:
        response = requests.post(url, files={"file": f}, headers=headers)
    data = response.json()
    file_id = data["data"]["id"]
    return get_report(file_id)

def scan_url(link):
    url = "https://www.virustotal.com/api/v3/urls"
    headers = {"x-apikey": VT_API_KEY}
    data = {"url": link}
    response = requests.post(url, data=data, headers=headers)
    url_id = response.json()["data"]["id"]
    return get_report(url_id, report_type="urls")

def get_report(resource_id, report_type="files"):
    headers = {"x-apikey": VT_API_KEY}
    url = f"https://www.virustotal.com/api/v3/{report_type}/{resource_id}"
    response = requests.get(url, headers=headers)
    data = response.json()
    stats = data["data"]["attributes"]["last_analysis_stats"]
    total_detections = stats["malicious"] + stats["suspicious"]
    if total_detections > 0:
        engines = data["data"]["attributes"]["last_analysis_results"]
        threats = [f"{e}: {r['result']}" for e, r in engines.items() if r["category"] in ["malicious", "suspicious"]]
        detail_url = f"https://www.virustotal.com/gui/{report_type}/{resource_id}"
        return f"⚠️ Menace détectée par {total_detections} moteurs :\n{detections}"
" + "\n".join(threats[:10]) + f"\n\n🔗 [Voir le rapport]({detail_url})"
    else:
        detail_url = f"https://www.virustotal.com/gui/{report_type}/{resource_id}"
        return f"✅ Aucune menace détectée !\n\n🔗 [Voir le rapport]({detail_url})"

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()

if __name__ == "__main__":
    main()
