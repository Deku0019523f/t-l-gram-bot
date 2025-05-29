
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

ADMIN_USERNAME = "@deku225"
PRODUCTS_FILE = "products.json"
PAYMENT_NUMBERS = """🌐 *Méthodes de paiement disponibles :*
- Wave : `+2250575719113`
- Orange : `+2250718623773`
- MTN : `+2250596430369`
"""

products = {}

def load_products():
    global products
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, "r") as f:
            products = json.load(f)
    else:
        products = {}

def save_products():
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(products, f, indent=4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bienvenue dans la boutique ! Utilisez /produits pour voir les articles disponibles.")

async def produits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not products:
        await update.message.reply_text("Aucun produit disponible pour le moment.")
        return
    for pid, p in products.items():
        promo_label = "🔥 Promo " if p.get("promo") else ""
        message = f"*{promo_label}{p['nom']}*
💰 Prix : {p['prix']} FCFA
🆔 ID : `{pid}`"
        keyboard = [[InlineKeyboardButton("Commander", callback_data=f"order_{pid}")]]
        await update.message.reply_markdown(message, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("order_"):
        pid = data.split("_")[1]
        if pid in products:
            p = products[pid]
            msg = f"""
🛒 *Commande de {p['nom']}*
💰 Prix : {p['prix']} FCFA
🆔 ID : `{pid}`

{PAYMENT_NUMBERS}

Après paiement, envoyez l'ID de transaction :
Format : ID - Moyen de paiement - Produit
Exemple : `TX123456 - Orange - {p['nom']}`
"""
            await query.message.reply_markdown(msg)

async def recevoir_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if "-" not in text:
        return
    parts = text.split(" - ")
    if len(parts) != 3:
        return
    txid, method, produit = parts
    receipt = (
        "🧾 *Reçu de Commande*
"
        f"🔐 Transaction ID : `{txid}`
"
        f"💳 Moyen : {method}
"
        f"📦 Produit : {produit}
"
        f"👤 Client : @{update.effective_user.username}
"
    )
    await update.message.reply_markdown(receipt)

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != ADMIN_USERNAME:
        await update.message.reply_text("Accès refusé.")
        return
    cmds = "/add nom - prix\n/del id\n/promo id\n/unpromo id"
    await update.message.reply_text(f"Commandes admin disponibles :
{cmds}")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != ADMIN_USERNAME:
        return
    try:
        txt = update.message.text[5:].strip()
        nom, prix = txt.split(" - ")
        pid = str(len(products) + 1)
        products[pid] = {"nom": nom.strip(), "prix": prix.strip(), "promo": False}
        save_products()
        await update.message.reply_text(f"Produit ajouté avec ID {pid}")
    except:
        await update.message.reply_text("Format invalide. Utilisez : /add nom - prix")

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != ADMIN_USERNAME:
        return
    pid = update.message.text[5:].strip()
    if pid in products:
        del products[pid]
        save_products()
        await update.message.reply_text("Produit supprimé.")
    else:
        await update.message.reply_text("ID introuvable.")

async def promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != ADMIN_USERNAME:
        return
    pid = update.message.text[6:].strip()
    if pid in products:
        products[pid]["promo"] = True
        save_products()
        await update.message.reply_text("Produit en promo.")
    else:
        await update.message.reply_text("ID introuvable.")

async def unpromo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != ADMIN_USERNAME:
        return
    pid = update.message.text[9:].strip()
    if pid in products:
        products[pid]["promo"] = False
        save_products()
        await update.message.reply_text("Promo retirée.")
    else:
        await update.message.reply_text("ID introuvable.")

async def avis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merci pour votre avis 🙏")

load_products()

app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("produits", produits))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("del", delete))
app.add_handler(CommandHandler("promo", promo))
app.add_handler(CommandHandler("unpromo", unpromo))
app.add_handler(CommandHandler("avis", avis))
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recevoir_transaction))

print("✅ Bot en ligne !")
app.run_polling()
    
