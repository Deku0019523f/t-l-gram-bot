import os
import logging
import requests
from flask import Flask, request
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
VT_API_KEY = os.getenv("VT_API_KEY")
CHANNEL_USERNAME = "@deku225"  # utilisé pour l'invitation au canal
ADMIN_ID = 1299831974

# Set up logging
logging.basicConfig(level=logging.INFO)

# Base de données temporaire en mémoire
users = set()
scan_history = []

# Bot setup
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Flask admin interface
web = Flask(__name__)

@web.route("/")
def index():
    return "Bot Telegram - Interface Web"

@web.route("/admin/send", methods=["POST"])
def admin_send():
    msg = request.form.get("message", "")
    for uid in users:
        try:
            app.bot.send_message(chat_id=uid, text=msg)
        except:
            pass
    return "Message envoyé à tous les utilisateurs."

@web.route("/admin/stats")
def admin_stats():
    return {
        "total_users": len(users),
        "total_scans": len(scan_history)
    }

# Vérifie l'abonnement
async def is_subscribed(user_id: int) -> bool:
    try:
        member = await app.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'creator', 'administrator']
    except:
        return False

# Message de bienvenue
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await is_subscribed(user.id):
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("S'abonner", url="https://t.me/+up78ma0Ev642YWM0")]])
        await update.message.reply_text(
            "Veuillez vous abonner à notre canal pour utiliser ce bot.",
            reply_markup=keyboard
        )
        return
    users.add(user.id)
    await update.message.reply_text("Bienvenue sur le bot de @deku225, vous pouvez m'envoyer vos liens et APK suspects pour les analyser.")

# Traitement des messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await is_subscribed(user.id):
        return

    if update.message.document:
        doc = update.message.document
        if not doc.file_name.endswith(".apk"):
            await update.message.reply_text("Veuillez envoyer un fichier .apk valide.")
            return
        file = await doc.get_file()
        path = f"/tmp/{doc.file_unique_id}.apk"
        await file.download_to_drive(path)
        result = scan_file(path)
    elif update.message.text and update.message.text.startswith("http"):
        result = scan_url(update.message.text)
    else:
        await update.message.reply_text("Veuillez envoyer un fichier APK ou un lien.")
        return

    scan_history.append((user.id, result))
    await update.message.reply_text(result, disable_web_page_preview=True)

# Analyse de fichier
def scan_file(file_path):
    url = "https://www.virustotal.com/api/v3/files"
    headers = {"x-apikey": VT_API_KEY}
    with open(file_path, "rb") as f:
        resp = requests.post(url, headers=headers, files={"file": f})
    data = resp.json()
    analysis_id = data["data"]["id"]

    # Récupération des résultats
    report_url = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"
    r = requests.get(report_url, headers=headers)
    res = r.json()
    stats = res["data"]["attributes"]["stats"]
    total_detections = stats["malicious"] + stats["suspicious"]
    threats = []
    if "results" in res["data"]["attributes"]:
        for engine, result in res["data"]["attributes"]["results"].items():
            if result.get("category") in ["malicious", "suspicious"]:
                threats.append(f"- {engine}: {result.get('result')}")

    detail_url = f"https://www.virustotal.com/gui/file/{res['meta']['file_info']['sha256']}/detection"
    if total_detections == 0:
        return f"✅ Aucune menace détectée !\nFichier sûr selon {len(res['data']['attributes']['results'])} moteurs.\n\n🔗 [Voir le rapport]({detail_url})"
    else:
        return (
            f"⚠️ Menace détectée par {total_detections} moteurs :\n"
            + "\n".join(threats[:10])
            + f"\n\n🔗 [Voir le rapport]({detail_url})"
        )

# Analyse de lien
def scan_url(link):
    url = "https://www.virustotal.com/api/v3/urls"
    headers = {"x-apikey": VT_API_KEY}
    data = {"url": link}
    response = requests.post(url, headers=headers, data=data)
    res = response.json()
    analysis_id = res["data"]["id"]

    # Rapport
    report_url = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"
    r = requests.get(report_url, headers=headers)
    result = r.json()
    stats = result["data"]["attributes"]["stats"]
    total = stats["malicious"] + stats["suspicious"]

    detail_url = f"https://www.virustotal.com/gui/url/{analysis_id.replace('-', '')}/detection"

    if total == 0:
        return f"✅ Aucun problème détecté avec ce lien.\n\n🔗 [Voir le rapport complet]({detail_url})"
    else:
        return f"⚠️ Ce lien a été détecté comme suspect par {total} moteurs.\n\n🔗 [Voir le rapport complet]({detail_url})"

# Handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.ALL, handle_message))

if __name__ == "__main__":
    import threading
    threading.Thread(target=web.run, kwargs={"host": "0.0.0.0", "port": 8080}).start()
    app.run_polling()
