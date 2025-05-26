import os
import logging
import requests
import json
from flask import Flask, request
from telegram import Update, InputFile
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
CHANNEL_USERNAME = "@deku225"  # ou le nom réel de ton canal

# Initialisation
logging.basicConfig(level=logging.INFO)
application = Application.builder().token(BOT_TOKEN).build()
flask_app = Flask(__name__)

# Route de test pour Render
@flask_app.route("/", methods=["GET"])
def home():
    return "Bot actif."

# Vérifie si l'utilisateur est abonné au canal
async def check_subscription(user_id: int) -> bool:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
    params = {"chat_id": CHANNEL_USERNAME, "user_id": user_id}
    try:
        response = requests.get(url, params=params).json()
        status = response.get("result", {}).get("status", "")
        return status in ["member", "administrator", "creator"]
    except Exception:
        return False

# Commande /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_subscription(user_id):
        await update.message.reply_text("Veuillez rejoindre le canal pour utiliser le bot : https://t.me/+up78ma0Ev642YWM0")
        return

    await update.message.reply_text(
        "Bienvenue sur le bot de @deku225 ! Vous pouvez m'envoyer vos liens et APK suspects pour les analyser."
    )

# Gestion des messages (liens ou fichiers APK)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_subscription(user_id):
        await update.message.reply_text("Veuillez rejoindre le canal pour utiliser le bot : https://t.me/+up78ma0Ev642YWM0")
        return

    if update.message.document:
        file = await context.bot.get_file(update.message.document.file_id)
        file_path = f"/tmp/{update.message.document.file_name}"
        await file.download_to_drive(file_path)
        await update.message.reply_text("Analyse de votre APK en cours...")
        result = analyse_virus_total(file_path)
        await update.message.reply_text(result)

    elif update.message.text and update.message.text.startswith("http"):
        await update.message.reply_text("Analyse de votre lien en cours...")
        result = analyse_virus_total(update.message.text)
        await update.message.reply_text(result)

# Analyse VirusTotal (exemple simplifié)
def analyse_virus_total(path_or_url: str) -> str:
    # Simule une réponse VirusTotal ici (à remplacer par ton API réelle)
    return "Analyse terminée. Résultat : Aucun malware détecté."  # ou retourner les détections

# Handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.ALL, handle_message))

# Lancement webhook
if __name__ == "__main__":
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        webhook_url=RENDER_EXTERNAL_URL,
        web_app=flask_app
)
