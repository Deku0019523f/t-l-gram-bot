from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Configuration
OWNER_USERNAME = "@deku225"
PAYMENT_NUMBERS = {
    "Orange": "+225 0718623773",
    "MTN": "+225 0596430369",
    "Wave": "+225 0575719113"
}
PROMO_PRODUCTS = ["Abonnement-IPTV-1mois"]

products = [
    {"title": "Internet Orange CI - 80 Go", "price": 8000, "category": "Abonnement"},
    {"title": "Internet Orange CI - 100 Go", "price": 13000, "category": "Abonnement"},
    {"title": "Internet Orange CI - 48 Go", "price": 6500, "category": "Abonnement"},
    {"title": "BOOSTAGE TIKTOK - 1000 abonnés", "price": 1500, "category": "Abonnement"},
    {"title": "BOOSTAGE YOUTUBE - 1000 abonnés", "price": 5000, "category": "Abonnement"},
    {"title": "BOOSTAGE INSTAGRAM - 1000 abonnés", "price": 1000, "category": "Abonnement"},
    {"title": "Netflix - 1 mois", "price": 2400, "category": "Abonnement"},
    {"title": "Netflix - 3 mois", "price": 7000, "category": "Abonnement"},
    {"title": "Abonnement-IPTV-1mois", "price": 1500, "category": "Abonnement"},
    {"title": "Abonnement-IPTV-3mois", "price": 8000, "category": "Abonnement"},
    {"title": "VPS 2GB RAM", "price": 2500, "category": "Abonnement"},
    {"title": "VPS 4GB RAM", "price": 4000, "category": "Abonnement"},
    {"title": "TikTok français monétiser", "price": 5000, "category": "abonnement"},
    {"title": "Logiciel d’espionnage", "price": 3000, "category": "Logiciel"},
    {"title": "Script Chumogh SSH #SLOWDNS", "price": 5000, "category": "Logiciel"},
    {"title": "Script + VPS pour WhatsApp Bot", "price": 3000, "category": "Logiciel"},
    {"title": "Hack caméra frontale avec Termux", "price": 2000, "category": "Logiciel"},
    {"title": "Outils de Phishing avec Termux", "price": 3000, "category": "Logiciel"}
]

user_orders = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("🛍️ Produits", callback_data="products")],
        [InlineKeyboardButton("📝 Avis", callback_data="avis")],
        [InlineKeyboardButton("📞 Contacter un agent", url="https://t.me/deku225")],
    ]
    welcome_text = (
        f"Bienvenue {user.mention_html()} dans la boutique officielle Deku 🧩 !\n"
        f"Voici ce que tu peux faire ci-dessous 👇\n\n"
        "Ce bot vous permet de commander et recevoir vos produits instantanément après paiement.\n"
        f"Contact : {OWNER_USERNAME}"
    )
    await update.message.reply_html(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    for product in products:
        title = f"🔥 Promo - {product['title']}" if product["title"] in PROMO_PRODUCTS else product["title"]
        text = f"📦 <b>{title}</b>\n💰 Prix : {product['price']} FCFA\n📂 Catégorie : {product['category']}"
        keyboard = [[InlineKeyboardButton("🛒 Commander", callback_data=f"order|{product['title']}")]]
        await query.message.reply_html(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data.startswith("order|"):
        _, product_name = query.data.split("|")
        user_orders[query.from_user.id] = product_name
        await query.answer()
        text = (
            f"🛍️ Vous avez sélectionné : <b>{product_name}</b>\n"
            "Veuillez envoyer l’ID de la transaction accompagné du moyen de paiement (Orange / MTN / Wave).\n\n"
            f"Exemple : `Orange 12345678`\n\n"
            f"Numéros pour paiement :\n"
            f"• Orange : {PAYMENT_NUMBERS['Orange']}\n"
            f"• MTN : {PAYMENT_NUMBERS['MTN']}\n"
            f"• Wave : {PAYMENT_NUMBERS['Wave']}"
        )
        await query.message.reply_html(text)
    elif query.data == "products":
        await show_products(update, context)
    elif query.data == "avis":
        await query.answer("Merci de laisser un avis positif 🙏")

async def handle_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_orders:
        return await update.message.reply_text("Veuillez d’abord choisir un produit avec 🛒 Commander.")
    
    try:
        parts = update.message.text.strip().split(" ")
        method = parts[0]
        tx_id = parts[1]
    except:
        return await update.message.reply_text("Format invalide. Utilisez par exemple : Orange 12345678")
    
    produit = user_orders.pop(user_id)
    reçu = (
        f"✅ *REÇU DE COMMANDE*\n\n"
        f"• Produit : {produit}\n"
        f"• Paiement via : {method}\n"
        f"• ID de transaction : `{tx_id}`\n\n"
        f"Merci de copier ce reçu et de l’envoyer à {OWNER_USERNAME}."
    )
    await update.message.reply_markdown(reçu)

if __name__ == "__main__":
    import os
    TOKEN = os.environ.get("BOT_TOKEN")  # à définir dans Railway

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_transaction))

    app.run_polling()
