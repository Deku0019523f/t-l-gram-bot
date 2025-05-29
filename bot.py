import os
import json
from datetime import datetime
from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))

PRODUCTS_FILE = "products.json"
user_states = {}

def load_products():
    if not os.path.exists(PRODUCTS_FILE):
        return []
    with open(PRODUCTS_FILE, "r") as f:
        return json.load(f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("/produits")],
        [KeyboardButton("/avis")],
        [KeyboardButton("/contact")],
    ]
    if update.effective_user.id == ADMIN_CHAT_ID:
        keyboard.append([KeyboardButton("/admin")])

    await update.message.reply_text(
        "🛍️ *Bienvenue sur Deku225-shop !*\nVoici les commandes disponibles :",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def produits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    produits = load_products()
    for p in produits:
        promo_label = "🔥 Promo : " if p.get("promo") else ""
        price = f"{p['price']} FCFA"
        message = f"*{promo_label}{p['title']}*\n💰 Prix : {price}"
        button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🛒 Commander", callback_data=f"buy_{p['title']}")]]
        )
        await update.message.reply_text(message, parse_mode="Markdown", reply_markup=button)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("buy_"):
        product = data[4:]
        user_states[query.from_user.id] = product
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
    transaction_id = update.message.text.strip()

    if user_id in user_states:
        product = user_states.pop(user_id)
        await update.message.reply_text(
            f"Deku225-shop:\n✅ Commande pour *{product}* reçue avec l'ID : `{transaction_id}`.\n"
            f"⏳ En attente de validation par l’admin.",
            parse_mode="Markdown"
        )
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=(
                f"📥 *Nouvelle commande à valider*\n"
                f"👤 Client : @{update.effective_user.username or update.effective_user.first_name}\n"
                f"🛒 Produit : *{product}*\n"
                f"💳 ID transaction : `{transaction_id}`\n"
                f"🕒 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
            ),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❗ Aucun produit sélectionné. Utilise /produits pour recommencer.")

async def avis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⭐ *Avis clients* :\n– Super service !\n– Livraison rapide !", parse_mode="Markdown")

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📩 Contacte @deku225 pour toute question.")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Accès refusé.")
        return
    await update.message.reply_text("🔧 Menu admin (fonctionnalités à venir).")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("produits", produits))
    app.add_handler(CommandHandler("avis", avis))
    app.add_handler(CommandHandler("contact", contact))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_transaction))

    print("✅ Bot lancé...")
    app.run_polling()

if __name__ == "__main__":
    main()
