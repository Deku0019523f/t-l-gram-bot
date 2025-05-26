import os
import requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
VT_API_KEY = os.getenv("VT_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

app = Flask(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_user_subscribed(user_id):
        await update.message.reply_text("Veuillez vous abonner à notre canal pour utiliser ce bot : https://t.me/+up78ma0Ev642YWM0")
        return

    await update.message.reply_text("Bienvenue sur le bot de @deku225 vous pouvez m'envoyer vos liens et apk suspect pour les analyser")

async def is_user_subscribed(user_id):
    url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={CHANNEL_ID}&user_id={user_id}"
    response = requests.get(url).json()
    status = response.get("result", {}).get("status", "")
    return status in ["member", "administrator", "creator"]

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document or update.message.document
    if file:
        file_path = await file.get_file()
        file_url = file_path.file_path
        response = requests.get(file_url)
        with open("sample.apk", "wb") as f:
            f.write(response.content)

        with open("sample.apk", "rb") as f:
            files = {"file": f}
            headers = {"x-apikey": VT_API_KEY}
            r = requests.post("https://www.virustotal.com/api/v3/files", files=files, headers=headers)
            analysis_id = r.json().get("data", {}).get("id")

        if analysis_id:
            report = get_report(analysis_id)
            await update.message.reply_text(report)
        else:
            await update.message.reply_text("Erreur lors de l'envoi du fichier à VirusTotal.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    headers = {"x-apikey": VT_API_KEY}
    data = {"url": url}
    r = requests.post("https://www.virustotal.com/api/v3/urls", data=data, headers=headers)
    analysis_id = r.json().get("data", {}).get("id")

    if analysis_id:
        report = get_report(analysis_id, url=True)
        await update.message.reply_text(report)
    else:
        await update.message.reply_text("Erreur lors de l'analyse du lien.")

def get_report(analysis_id, url=False):
    headers = {"x-apikey": VT_API_KEY}
    url_path = "urls" if url else "files"
    response = requests.get(f"https://www.virustotal.com/api/v3/analyses/{analysis_id}", headers=headers).json()

    try:
        result = response["data"]["attributes"]["results"]
        total_detections = sum(1 for engine in result.values() if engine["category"] == "malicious")
        threats = [f"{engine}: {info['result']}" for engine, info in result.items() if info["category"] == "malicious"]

        detail_url = f"https://www.virustotal.com/gui/{url_path}/{analysis_id}"
        if total_detections == 0:
            return "✅ Aucun moteur n'a détecté de menace."
        else:
            return (
                f"⚠️ Menace détectée par {total_detections} moteurs:\n"
                + "\n".join(threats[:10]) +
                f"\n\n🔗 [Voir le rapport]({detail_url})"
            )
    except Exception as e:
        return f"Erreur lors de l'analyse: {e}"

if __name__ == "__main__":
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        webhook_url=os.environ.get("RENDER_EXTERNAL_URL")
    )
