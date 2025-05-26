import os
import logging
import hashlib
import aiohttp
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
VT_API_KEY = os.getenv("VT_API_KEY")
ADMIN_ID = 1299831974

# Configurer le logging
logging.basicConfig(level=logging.INFO)

# Stock temporaire pour les analyses (en mémoire)
scan_history = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bienvenue ! Envoyez un fichier APK pour analyse.")

def get_file_hash(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

async def upload_and_scan(file_path):
    hash_sha256 = get_file_hash(file_path)
    headers = {"x-apikey": VT_API_KEY}
    async with aiohttp.ClientSession() as session:
        # Vérifier si le fichier est déjà connu
        url_report = f"https://www.virustotal.com/api/v3/files/{hash_sha256}"
        async with session.get(url_report, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data

        # Sinon, on l'upload
        with open(file_path, "rb") as f:
            files = {'file': f}
            upload_url = "https://www.virustotal.com/api/v3/files"
            async with session.post(upload_url, headers=headers, data=files) as upload_resp:
                if upload_resp.status == 200:
                    uploaded = await upload_resp.json()
                    file_id = uploaded["data"]["id"]

        # Obtenir le rapport via l'ID
        async with session.get(f"https://www.virustotal.com/api/v3/analyses/{file_id}", headers=headers) as analysis_resp:
            return await analysis_resp.json()

def format_result(data):
    if "data" not in data or "attributes" not in data["data"]:
        return "Analyse en cours ou invalide."

    attr = data["data"]["attributes"]
    stats = attr["stats"]
    total = sum(stats.values())
    detected = stats.get("malicious", 0) + stats.get("suspicious", 0)

    details = ""
    if "results" in attr:
        for engine, result in attr["results"].items():
            if result["category"] in ("malicious", "suspicious"):
                details += f"- {engine}: {result['result']}\n"

    permalink = f"https://www.virustotal.com/gui/file/{attr['sha256']}/detection"
    summary = f"""
Résultat de l'analyse :

{'⚠️' if detected else '✅'} {'Menace détectée !' if detected else 'Aucune menace détectée !'}
Moteurs détectant une menace : {detected}/{total}

{details if details else 'Aucune menace détaillée fournie.'}

🔗 Rapport complet : {permalink}
"""
    return summary.strip()

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc or not doc.file_name.endswith(".apk"):
        await update.message.reply_text("Veuillez envoyer un fichier APK.")
        return

    file = await context.bot.get_file(doc.file_id)
    file_path = f"/tmp/{doc.file_name}"
    await file.download_to_drive(file_path)

    result = await upload_and_scan(file_path)
    text = format_result(result)

    # Log pour admin
    scan_history.append({
        "user": update.message.from_user.username,
        "filename": doc.file_name,
        "datetime": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "result": text
    })

    await update.message.reply_text(text)

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("Accès refusé.")
        return

    if not scan_history:
        await update.message.reply_text("Aucune analyse enregistrée.")
        return

    last = scan_history[-5:]
    msg = "\n\n".join(
        f"Utilisateur : @{entry['user']}\nFichier : {entry['filename']}\nDate : {entry['datetime']}\n{entry['result']}"
        for entry in last
    )
    await update.message.reply_text(f"Dernières analyses :\n\n{msg}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.run_polling()
