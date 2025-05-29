import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "deku225")
PRODUCTS_FILE = "products.json"

def is_admin(update: Update) -> bool:
    return update.effective_user.username == ADMIN_USERNAME

def load_products():
    with open(PRODUCTS_FILE, "r") as f:
        return json.load(f)

def save_products(products):
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(products, f, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛍 Voir les produits", callback_data="products")],
        [InlineKeyboardButton("⭐ Voir les avis", callback_data="avis")],
        [InlineKeyboardButton("👤 Contacter un agent", url="https://t.me/deku225")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        """
🎉 Bienvenue sur Informatique Shop !

📦 Produits : Abonnements internet, IPTV, Netflix, TikTok boost, etc.
💳 Paiement : Orange Money / Moov / Wave
✉️ Contact : @deku225

Cliquez ci-dessous pour voir les produits, les avis et contacter un agent ⬇️
""",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "products":
        products = load_products()
        for i, p in enumerate(products):
            promo_label = "🔥 Promo " if p.get("promo") else ""
            message = f"*{promo_label}{p['title']}*
💰 Prix : {p['price']} FCFA"
            keyboard = [[InlineKeyboardButton("Commander", callback_data=f"order_{i}")]]
            await query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    elif query.data == "avis":
        await query.message.reply_text("📢 Voici quelques avis de nos clients :\n⭐ ⭐ ⭐ ⭐ ⭐ Très satisfait !\n⭐ ⭐ ⭐ ⭐ Service rapide et efficace !")

async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    index = int(query.data.split("_")[1])
    products = load_products()
    product = products[index]
    await query.message.reply_text(
        f"🛍 *Commande :* {product['title']}\n💵 *Prix :* {product['price']} FCFA\n\nVeuillez choisir un mode de paiement et envoyer l'identifiant de la transaction.\n\nModes de paiement :\nWave : +2250575719113\nOrange : +2250718623773\nMTN : +2250596430369",
        parse_mode="Markdown"
    )
    context.user_data['current_order'] = product

async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'current_order' in context.user_data:
        product = context.user_data['current_order']
        transaction_id = update.message.text
        message = f"""
🧾 *Reçu de Commande*

👤 Client : @{update.effective_user.username}
📦 Produit : {product['title']}
💵 Prix : {product['price']} FCFA
🧾 Transaction : `{transaction_id}`

Merci pour votre commande 🙏
        """
        await update.message.reply_text(message, parse_mode="Markdown")
        context.user_data.clear()

# Admin Commands

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Accès refusé. Tu n'es pas admin.")
        return
    keyboard = [
        [InlineKeyboardButton("➕ Ajouter un produit", callback_data="admin_add")],
        [InlineKeyboardButton("🗑 Supprimer un produit", callback_data="admin_delete")],
        [InlineKeyboardButton("🔥 Activer/Désactiver promo", callback_data="admin_promo")],
    ]
    await update.message.reply_text("🔧 Menu admin :", reply_markup=InlineKeyboardMarkup(keyboard))

# Attach all handlers
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CallbackQueryHandler(handle_buttons, pattern="^(products|avis)$"))
app.add_handler(CallbackQueryHandler(handle_order, pattern="^order_\\d+$"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_payment))

if __name__ == '__main__':
    app.run_polling()
    
