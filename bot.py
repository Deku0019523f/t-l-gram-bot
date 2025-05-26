import os
import logging
import aiohttp
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, CallbackQueryHandler
)

# Configurations
BOT_TOKEN = os.environ.get("BOT_TOKEN")
VT_API_KEY = os.environ.get("VT_API_KEY")
ADMIN_ID = 1299831974
CHANNEL_USERNAME = "@deku225channel"
CHANNEL_ID = "-1002261675803"  # à adapter si besoin

app = Flask(__name__)
users = set()

# Log
logging.basicConfig(level=logging.INFO)

# Vérifie si l'utilisateur est abonné
async def is_subscribed(user_id):
    try:
        member = await application.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await is_subscribed(user.id):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("S'abonner", url="https://t.me/+up78ma0Ev642YWM0")],
            [InlineKeyboardButton("✅ J'ai rejoint", callback_data="check_sub")]
        ])
        await update.message.reply_text(
            "Veuillez vous abonner à notre canal pour utiliser ce bot.",
            reply_markup=keyboard
        )
        return
    users.add(user.id)
    await update.message.reply_text(
        "Bienvenue sur le bot de @deku225, vous pouvez m'envoyer vos liens et APK suspects pour les analyser."
    )

# Vérification d'abonnement après clic
async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if await is_subscribed(user_id):
        users.add(user_id)
        await query.edit_message_text("Merci d'avoir rejoint ! Envoyez un fichier ou un lien à analyser.")
    else:
        await query.answer("Vous n'avez pas encore rejoint le canal.", show_alert=True)

# Analyse d'un fichier
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update.effective_user.id):
        return await update.message.reply_text("Abonnez-vous d'abord au canal pour utiliser ce bot.")
    document = update.message.document
    if not document.file_name.endswith(".apk"):
        return await update.message.reply_text("Ce fichier n'est pas un APK.")
    file = await document.get_file()
    file_path = f"/tmp/{document.file_name}"
    await file.download_to_drive(file_path)
    result = await scan_file(file_path)
    await update.message.reply_text(result)

# Analyse d'un lien
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update.effective_user.id):
        return await update.message.reply_text("Abonnez-vous d'abord au canal pour utiliser ce bot.")
    text = update.message.text
    if text.startswith("http"):
        result = await scan_url(text)
        await update.message.reply_text(result)

# Fonction scan fichier
async def scan_file(file_path):
    headers = {"x-apikey": VT_API_KEY}
    async with aiohttp.ClientSession() as session:
        with open(file_path, "rb") as f:
            files = {"file": f}
            async with session.post("https://www.virustotal.com/api/v3/files", headers=headers, data=files) as resp:
                data = await resp.json()
                file_id = data["data"]["id"]
        async with session.get(f"https://www.virustotal.com/api/v3/analyses/{file_id}", headers=headers) as resp:
            result = await resp.json()
            return format_result(result)

# Fonction scan lien
async def scan_url(url):
    headers = {"x-apikey": VT_API_KEY}
    async with aiohttp.ClientSession() as session:
        data = {"url": url}
        async with session.post("https://www.virustotal.com/api/v3/urls", headers=headers, data=data) as resp:
            res = await resp.json()
            url_id = res["data"]["id"]
        async with session.get(f"https://www.virustotal.com/api/v3/analyses/{url_id}", headers=headers) as resp:
            result = await resp.json()
            return format_result(result)

# Formatage du résultat
def format_result(data):
    stats = data["data"]["attributes"]["stats"]
    total_detections = stats["malicious"] + stats["suspicious"]
    detail_url = f"https://www.virustotal.com/gui/file/{data['meta']['file_info']['sha256']}" if "file_info" in data["meta"] else "https://www.virustotal.com"
    threats = []
    for engine, res in data["data"]["attributes"]["results"].items():
        if res["category"] in ["malicious", "suspicious"]:
            threats.append(f"- {engine}: {res['result']}")
    if total_detections > 0:
        return f"⚠️ Menace détectée par {total_detections} moteurs:\n" + "\n".join(threats[:10]) + f"\n\n🔗 [Voir le rapport]({detail_url})"
    return f"✅ Aucune menace détectée !\nFichier ou lien sûr selon {stats['undetected']} moteurs.\n\n🔗 [Voir le rapport]({detail_url})"

# Interface admin
@app.route("/admin", methods=["GET"])
def admin_home():
    return f"<h2>Bienvenue admin</h2><p>Utilisateurs : {len(users)}</p><form method='post'><input name='msg'><button>Envoyer</button></form>"

@app.route("/admin", methods=["POST"])
def admin_send():
    msg = request.form["msg"]
    for uid in users:
        try:
            application.bot.send_message(chat_id=uid, text=f"[ADMIN] {msg}")
        except:
            pass
    return "<p>Message envoyé</p><a href='/admin'>Retour</a>"

if __name__ == "__main__":
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(check_subscription, pattern="check_sub"))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.run_webhook(listen="0.0.0.0", port=int(os.environ.get("PORT", 5000)), webhook_url=os.environ.get("RENDER_EXTERNAL_URL"))
