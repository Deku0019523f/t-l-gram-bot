import json
import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes,
    filters, CallbackQueryHandler
)
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME") or "Deku225"

logging.basicConfig(level=logging.INFO)

products_file = "products.json"
pending_orders = {}

def load_products():
    with open(products_file, "r") as f:
        return json.load(f)

def save_products(products):
    with open(products_file, "w") as f:
        json.dump(products, f, indent=4)

def format_product(p):
    promo_label = "🔥 Promo : " if p.get("promo") else ""
    return f"*{promo_label}{p['title']}*\n💰 Prix : {p['price']} FCFA"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["/produits", "/avis"],
        ["/admin", "/contact"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "🛍️ *Bienvenue sur Deku225-shop !*\n"
        "Voici les commandes disponibles :\n\n"
        "• /produits – Voir les produits\n"
        "• /avis – Lire les avis clients\n"
        "• /admin – Gérer la boutique (admin uniquement)\n"
        "• /contact – Contacter un agent",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def produits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products = load_products()
    for p in products:
        keyboard = [[InlineKeyboardButton("🛒 Commander", callback_data=f"buy_{p['title']}")]]
        await update.message.reply_text(
            format_product(p),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("buy_"):
        product = query.data.replace("buy_", "")
        user_id = query.from_user.id
        pending_orders[user_id] = product
        await query.message.reply_text(
            f"Deku225-shop:\n📝 Tu as choisi *{product}*.\n\n"
            "💵 Pour valider ta commande, effectue un dépôt sur l’un des numéros suivants :\n\n"
            "📱 Wave : +2250575719113\n"
            "📱 Orange Money : +2250718623773\n"
            "📱 MTN : +2250596430369\n\n"
            "Ensuite, envoie l'ID de ta transaction ici pour confirmer ton achat.",
            parse_mode="Markdown"
        )

async def handle_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in pending_orders:
        product = pending_orders.pop(user_id)
        transaction_id = update.message.text.strip()
        await update.message.reply_text(
            f"Deku225-shop:\n✅ Commande pour *{product}* reçue avec l'ID : `{transaction_id}`.\n"
            f"⏳ En attente de validation par @{ADMIN_USERNAME}.",
            parse_mode="Markdown"
        )
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"📥 Nouvelle commande de {update.effective_user.full_name} (@{update.effective_user.username}):\n"
                 f"Produit : *{product}*\nTransaction ID : `{transaction_id}`",
            parse_mode="Markdown"
        )

async def avis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🗣️ Avis clients :\n⭐️⭐️⭐️⭐️⭐️ Excellent service !")

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📞 Pour toute assistance, contacte : @deku225")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    if username != ADMIN_USERNAME:
        await update.message.reply_text("❌ Accès refusé.")
        return

    await update.message.reply_text(
        "🔐 Menu Admin :\n"
        "/ajouter – Ajouter un produit\n"
        "/supprimer – Supprimer un produit\n"
        "/modifier – Modifier un produit\n"
        "/promo – Activer une promo"
    )

# Ajouter produit
async def ajouter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    if username != ADMIN_USERNAME:
        return
    msg = update.message.text.split(" ", 2)
    if len(msg) < 3:
        await update.message.reply_text("❌ Utilise /ajouter NomProduit Prix")
        return
    title, price = msg[1], msg[2]
    products = load_products()
    products.append({"title": title, "price": price})
    save_products(products)
    await update.message.reply_text(f"✅ Produit ajouté : {title} – {price} FCFA")

# Supprimer produit
async def supprimer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    if username != ADMIN_USERNAME:
        return
    title = update.message.text.replace("/supprimer ", "")
    products = load_products()
    new_products = [p for p in products if p["title"] != title]
    save_products(new_products)
    await update.message.reply_text(f"🗑️ Produit supprimé : {title}")

# Modifier produit
async def modifier(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    if username != ADMIN_USERNAME:
        return
    msg = update.message.text.split(" ", 3)
    if len(msg) < 4:
        await update.message.reply_text("❌ Utilise /modifier AncienTitre NouveauTitre NouveauPrix")
        return
    old, new, price = msg[1], msg[2], msg[3]
    products = load_products()
    for p in products:
        if p["title"] == old:
            p["title"] = new
            p["price"] = price
    save_products(products)
    await update.message.reply_text(f"✏️ Produit modifié : {old} → {new} – {price} FCFA")

# Activer promo
async def promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    if username != ADMIN_USERNAME:
        return
    title = update.message.text.replace("/promo ", "")
    products = load_products()
    for p in products:
        if p["title"] == title:
            p["promo"] = True
    save_products(products)
    await update.message.reply_text(f"🔥 Promo activée sur : {title}")

# Lancer le bot
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("produits", produits))
app.add_handler(CommandHandler("avis", avis))
app.add_handler(CommandHandler("contact", contact))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("ajouter", ajouter))
app.add_handler(CommandHandler("supprimer", supprimer))
app.add_handler(CommandHandler("modifier", modifier))
app.add_handler(CommandHandler("promo", promo))
app.add_handler(CallbackQueryHandler(handle_button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_transaction))

if __name__ == "__main__":
    print("Bot en ligne...")
    app.run_polling()
