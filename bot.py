import os
import requests
from langdetect import detect
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

BOT_TOKEN = '8071717887:AAFyXdPIagfBvurPZ8aLYRg4VlU61nTZ22E'
VT_API_KEY = '1131775d5d74f8457607cad7681f4ac68d904c176f9b1f6eeeb660374db398ed''

VT_FILE_URL = 'https://www.virustotal.com/api/v3/files'
VT_URL_SCAN = 'https://www.virustotal.com/api/v3/urls'
VT_URL_REPORT = 'https://www.virustotal.com/api/v3/analyses/{}'

headers = {"x-apikey": VT_API_KEY}

# Traductions pour les messages
MESSAGES = {
    "start": {
        "fr": "👋 *Bienvenue !*\n\nEnvoie-moi un lien ou un fichier APK, je l'analyserai.",
        "en": "👋 *Welcome!*\n\nSend me a link or an APK file, I’ll scan it for you.",
        "ja": "👋 *ようこそ！*\n\nリンクまたはAPKファイルを送ってください。ウイルスチェックします。"
    },
    "not_apk": {
        "fr": "❗ Ce n’est pas un fichier APK.",
        "en": "❗ This is not an APK file.",
        "ja": "❗ これはAPKファイルではありません。"
    },
    "file_ok": {
        "fr": "📦 Fichier reçu. Envoi à VirusTotal...",
        "en": "📦 File received. Uploading to VirusTotal...",
        "ja": "📦 ファイルを受信しました。VirusTotalに送信中..."
    },
    "url_ok": {
        "fr": "🔍 Analyse du lien en cours...",
        "en": "🔍 Scanning the link...",
        "ja": "🔍 リンクをスキャン中..."
    },
    "file_error": {
        "fr": "❌ Erreur lors de l’envoi du fichier.",
        "en": "❌ Error while uploading the file.",
        "ja": "❌ ファイルのアップロード中にエラーが発生しました。"
    },
    "url_error": {
        "fr": "❌ Erreur lors de l'analyse du lien.",
        "en": "❌ Error while scanning the link.",
        "ja": "❌ リンクのスキャン中にエラーが発生しました。"
    },
    "threat": {
        "fr": "⚠️ *Menace détectée !*\n{mal} moteurs sur {total} ont signalé une menace.\n\n🔗 [Voir le rapport]({url})",
        "en": "⚠️ *Threat detected!*\n{mal} engines out of {total} flagged this as malicious.\n\n🔗 [View report]({url})",
        "ja": "⚠️ *脅威が検出されました！*\n{total}中{mal}のエンジンが悪意のあるものとして検出しました。\n\n🔗 [レポートを見る]({url})"
    },
    "clean": {
        "fr": "✅ *Aucune menace détectée !*\nFichier ou lien sûr selon {total} moteurs.\n\n🔗 [Voir le rapport]({url})",
        "en": "✅ *No threats detected!*\nFile or link is clean according to {total} engines.\n\n🔗 [View report]({url})",
        "ja": "✅ *脅威は検出されませんでした！*\n{total}のエンジンによると安全です。\n\n🔗 [レポートを見る]({url})"
    },
    "report_fail": {
        "fr": "❌ Impossible de récupérer le rapport.",
        "en": "❌ Failed to retrieve report.",
        "ja": "❌ レポートの取得に失敗しました。"
    }
}

# Détection langue
def get_lang(text):
    try:
        lang = detect(text)
        return lang if lang in ["fr", "en", "ja"] else "fr"
    except:
        return "fr"

def msg(key, lang="fr", **kwargs):
    return MESSAGES[key][lang].format(**kwargs)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.message.text or "")
    await update.message.reply_text(msg("start", lang), parse_mode='Markdown')

# Lien
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.message.text)
    url = update.message.text
    await update.message.reply_text(msg("url_ok", lang))

    r = requests.post(VT_URL_SCAN, headers=headers, data={'url': url})
    if r.status_code != 200:
        await update.message.reply_text(msg("url_error", lang))
        return

    scan_id = r.json()['data']['id']
    report = requests.get(VT_URL_REPORT.format(scan_id), headers=headers)

    if report.status_code == 200:
        data = report.json()
        stats = data['data']['attributes']['stats']
        mal = stats.get('malicious', 0)
        total = sum(stats.values())
        vt_url = f"https://www.virustotal.com/gui/url/{scan_id}/detection"
        key = "threat" if mal > 0 else "clean"
        await update.message.reply_text(msg(key, lang, mal=mal, total=total, url=vt_url), parse_mode='Markdown')
    else:
        await update.message.reply_text(msg("report_fail", lang))

# Fichier APK
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.message.caption or "")
    doc = update.message.document
    if doc.mime_type != 'application/vnd.android.package-archive':
        await update.message.reply_text(msg("not_apk", lang))
        return

    await update.message.reply_text(msg("file_ok", lang))
    file = await doc.get_file()
    file_path = await file.download_to_drive()

    with open(file_path, 'rb') as f:
        r = requests.post(VT_FILE_URL, headers=headers, files={'file': f})
    if r.status_code != 200:
        await update.message.reply_text(msg("file_error", lang))
        return

    scan_id = r.json()['data']['id']
    report = requests.get(VT_URL_REPORT.format(scan_id), headers=headers)

    if report.status_code == 200:
        data = report.json()
        stats = data['data']['attributes']['stats']
        mal = stats.get('malicious', 0)
        total = sum(stats.values())
        vt_url = f"https://www.virustotal.com/gui/file/{scan_id}/detection"
        key = "threat" if mal > 0 else "clean"
        await update.message.reply_text(msg(key, lang, mal=mal, total=total, url=vt_url), parse_mode='Markdown')
    else:
        await update.message.reply_text(msg("report_fail", lang))

# Lancement du bot
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.run_polling()