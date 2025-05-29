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
        "🎉 Bienvenue sur *Informatique Shop* !\n\n"
        "📦 Produits : Abonnements internet, IPTV, TikTok boost, Netflix...\n"
        "💳 Paiement : Orange Money, Moov, Wave\n"
        f"📩 Contact : {ADMIN_USERNAME}\n\n"
        "Clique sur un bouton ci-dessous pour commencer 👇"
    )
    keyboard = [
        [InlineKeyboardButton("🛍 Voir les Produits", callback_data="products")],
        [InlineKeyboardButton("💬 Avis", callback_data="avis")],
        [InlineKeyboardButton("📩 Contacter un agent", url=f"https://t.me/{ADMIN_USERNAME.replace('@','')}")]
    ]
    await update.message.reply_text(message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# Afficher les produits
async def show_products(update: Update, context: CallbackContext):
    products = load_products()
    for p in products:
        promo = p.get("promo", False)
        promo_label = "🔥 Promo - " if promo and datetime.date.today() <= datetime.date.fromisoformat(p["promo_end"]) else ""
        title = f"{promo_label}{p['title']}"
        message = f"*{title}*\n💰 Prix : {p['price']} FCFA"
        keyboard = [[InlineKeyboardButton("🛒 Commander", callback_data=f"order_{p['title']}")]]
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# Gérer les callbacks
async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == "products":
        await show_products(update, context)
    elif query.data == "avis":
        await query.edit_message_text("💬 Pour laisser un avis, écris ton message ici. Merci ! 🙏")
    elif query.data.startswith("order_"):
        product_name = query.data.replace("order_", "")
        await query.message.reply_text(
            f"📝 Tu as choisi *{product_name}*.\n"
            "Envoie maintenant l'**ID de ta transaction** pour valider la commande.",
            parse_mode="Markdown"
        )
        context.user_data["last_order"] = product_name

# Recevoir l'ID de transaction
async def handle_message(update: Update, context: CallbackContext):
    username = update.effective_user.username
    if username and ADMIN_USERNAME and username.lower() == ADMIN_USERNAME.replace("@", "").lower():
        await handle_admin_message(update, context)
        return

    if "last_order" in context.user_data:
        product = context.user_data["last_order"]
        transaction_id = update.message.text.strip()
        receipt = (
            f"🧾 *Reçu de commande*\n"
            f"👤 Client : @{username or 'Inconnu'}\n"
            f"📦 Produit : {product}\n"
            f"🔐 ID Transaction : `{transaction_id}`\n"
            "✅ Merci pour ta commande !"
        )
        await update.message.reply_text(receipt, parse_mode="Markdown")
        context.user_data.clear()

# /admin
async def admin(update: Update, context: CallbackContext):
    username = update.effective_user.username
    if not username or username.lower() != ADMIN_USERNAME.replace("@", "").lower():
        await update.message.reply_text("⛔ Accès refusé.")
        return

    keyboard = [
        [InlineKeyboardButton("➕ Ajouter produit", callback_data="add")],
        [InlineKeyboardButton("📝 Modifier produit", callback_data="edit")],
        [InlineKeyboardButton("❌ Supprimer produit", callback_data="delete")]
    ]
    await update.message.reply_text("🛠 *Menu Admin* :", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# Messages d'admin
async def handle_admin_message(update: Update, context: CallbackContext):
    msg = update.message.text
    try:
        if msg.startswith("add:"):
            _, title, price, category = msg.split(":", 3)
            products = load_products()
            products.append({
                "title": title.strip(),
                "price": int(price),
                "category": category.strip()
            })
            save_products(products)
            await update.message.reply_text("✅ Produit ajouté.")
        elif msg.startswith("delete:"):
            _, title = msg.split(":", 1)
            products = load_products()
            products = [p for p in products if p["title"] != title.strip()]
            save_products(products)
            await update.message.reply_text("✅ Produit supprimé.")
        elif msg.startswith("edit:"):
            _, old_title, new_title, new_price = msg.split(":", 3)
            products = load_products()
            for p in products:
                if p["title"] == old_title.strip():
                    p["title"] = new_title.strip()
                    p["price"] = int(new_price)
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
