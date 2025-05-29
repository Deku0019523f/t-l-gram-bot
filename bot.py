import json
import os
import datetime
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackContext,
    MessageHandler, CallbackQueryHandler, filters
)

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")  # ex: "@deku225"

# Logger
logging.basicConfig(level=logging.INFO)

# Charger et sauvegarder les produits
def load_products():
    with open("products.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_products(products):
    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

# /start
async def start(update: Update, context: CallbackContext):
    message = (
        "🎉 Bienvenue sur Informatique Shop !\n\n"
        "📦 Produits : Abonnements internet, IPTV, Netflix, TikTok boost, etc.\n"
        "💳 Paiement : Orange Money / Moov / Wave\n"
        f"✉️ Contact : {ADMIN_USERNAME}\n\n"
        "Cliquez ci-dessous pour voir les produits, les avis et contacter un agent ⬇️"
    )
    keyboard = [
        [InlineKeyboardButton("🛍 Voir les Produits", callback_data="products")],
        [InlineKeyboardButton("💬 Avis", callback_data="avis")],
        [InlineKeyboardButton("📩 Contacter un agent", url=f"https://t.me/{ADMIN_USERNAME.replace('@','')}")]
    ]
    await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard))

# Afficher les produits
async def show_products(update: Update, context: CallbackContext):
    products = load_products()
    for p in products:
        promo = p.get("promo", False)
        promo_label = "🔥 Promo - " if promo and datetime.date.today() <= datetime.date.fromisoformat(p["promo_end"]) else ""
        msg = f"*{promo_label}{p['title']}*\nPrix : {p['price']} FCFA"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode="Markdown")

# Boutons
async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == "products":
        await show_products(update, context)
    elif query.data == "avis":
        await query.edit_message_text("🔖 Laissez-nous un avis par message ! Merci 🙏")

# /admin
async def admin(update: Update, context: CallbackContext):
    if update.effective_user.username != ADMIN_USERNAME.replace("@", ""):
        await update.message.reply_text("⛔ Accès refusé.")
        return
    keyboard = [
        [InlineKeyboardButton("➕ Ajouter produit", callback_data="add")],
        [InlineKeyboardButton("📝 Modifier produit", callback_data="edit")],
        [InlineKeyboardButton("❌ Supprimer produit", callback_data="delete")]
    ]
    await update.message.reply_text("🛠 Menu Admin :", reply_markup=InlineKeyboardMarkup(keyboard))

# Gérer les messages admin
async def handle_admin_message(update: Update, context: CallbackContext):
    if update.effective_user.username != ADMIN_USERNAME.replace("@", ""):
        return
    msg = update.message.text
    try:
        if msg.startswith("add:"):
            _, title, price, category = msg.split(":", 3)
            products = load_products()
            products.append({"title": title.strip(), "price": int(price), "category": category.strip()})
            save_products(products)
            await update.message.reply_text("✅ Produit ajouté.")
        elif msg.startswith("delete:"):
            _, title = msg.split(":", 1)
            products = load_products()
            products = [p for p in products if p["title"] != title.strip()]
            save_products(products)
            await update.message.reply_text("✅ Produit supprimé.")
        elif msg.startswith("edit:"):
            _, old_title, new_title, price = msg.split(":", 3)
            products = load_products()
            for p in products:
                if p["title"] == old_title.strip():
                    p["title"] = new_title.strip()
                    p["price"] = int(price)
                    break
            save_products(products)
            await update.message.reply_text("✅ Produit modifié.")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur : {e}")

# Lancer le bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_message))
    app.run_polling()
