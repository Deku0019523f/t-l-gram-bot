
import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")

PRODUCTS_FILE = "products.json"

def load_products():
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_products(products):
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛍️ Voir les produits", callback_data="show_products")],
        [InlineKeyboardButton("💬 Avis", callback_data="avis")],
        [InlineKeyboardButton("📞 Contacter un agent", url="https://t.me/deku225")]
    ]
    await update.message.reply_text(
        "🎉 Bienvenue sur Informatique Shop !\n\n"
        "📦 Produits : Abonnements internet, IPTV, Netflix, TikTok boost, etc.\n"
        "💳 Paiement : Orange Money / Moov / Wave\n"
        "✉️ Contact : @deku225\n\n"
        "Cliquez ci-dessous pour voir les produits, les avis et contacter un agent ⬇️",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    products = load_products()
    for p in products:
        promo_label = "🔥 Promo - " if p.get("promo") else ""
        message = f"*{promo_label}{p['title']}*\n💰 Prix : {p['price']} FCFA"
        keyboard = [[InlineKeyboardButton("🛒 Commander", callback_data=f"order_{p['title']}")]]
        await query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "show_products":
        await show_products(update, context)
    elif query.data == "avis":
        await query.message.reply_text("⭐ Laissez votre avis ici : https://t.me/deku225")
    elif query.data.startswith("order_"):
        product_name = query.data.replace("order_", "")
        context.user_data["last_order"] = product_name
        await query.message.reply_text(
            f"📝 Tu as choisi *{product_name}*.\n\n"
            "💵 Pour valider ta commande, effectue un dépôt sur l’un des numéros suivants :\n\n"
            "📱 Wave : +2250575719113\n"
            "📱 Orange Money : +2250718623773\n"
            "📱 MTN : +2250596430369\n\n"
            "Ensuite, *envoie l'ID de ta transaction ici* pour confirmer ton achat.",
            parse_mode="Markdown"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "last_order" in context.user_data:
        transaction_id = update.message.text
        product = context.user_data["last_order"]
        await update.message.reply_text(
            f"✅ Commande pour *{product}* reçue avec l'ID : `{transaction_id}`.\n"
            "⏳ En attente de validation par @deku225.",
            parse_mode="Markdown"
        )
        del context.user_data["last_order"]

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

if __name__ == "__main__":
    app.run_polling()
    
