from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import os

TOKEN = os.getenv("BOT_TOKEN")
USERNAME = "t.me/deku225"

products = [
    "💻 PC Gamer - 450,000 FCFA",
    "📱 iPhone 13 - 320,000 FCFA",
    "🎧 AirPods Pro - 95,000 FCFA"
]

payment_methods = '''💵 *Modes de paiement disponibles :*

📲 Orange Money : +225 0718623773
📲 MTN Mobile Money : +225 0575719113
🌊 Wave : +225 0596430369

Une fois le paiement effectué, envoyez l'identifiant de la transaction pour recevoir le nom d'utilisateur Telegram du vendeur.
'''

welcome_message = '''👋 Bonjour {username}, bienvenue dans notre boutique Telegram !

🛍️ Voici nos produits disponibles :
{products}

Merci de votre confiance !
'''

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.first_name or "Client"
    message = welcome_message.format(username=username, products='\n'.join(products))
    keyboard = [
        [InlineKeyboardButton("🛒 Commander", callback_data='order')],
        [InlineKeyboardButton("📝 Avis", callback_data='avis')],
        [InlineKeyboardButton("📞 Contacter un agent", callback_data='contact')],
        [InlineKeyboardButton("📦 Produits", callback_data='products')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == 'order':
        await query.edit_message_text(text="🧾 Veuillez effectuer le paiement :\n\n" + payment_methods, parse_mode="Markdown")
    elif data == 'avis':
        await query.edit_message_text(text="📝 Laissez votre avis ici : @deku225")
    elif data == 'contact':
        await query.edit_message_text(text="📞 Contactez un agent via Telegram : @deku225")
    elif data == 'products':
        await query.edit_message_text(text="📦 Produits disponibles :\n\n" + '\n'.join(products))

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()