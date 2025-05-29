import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1299831974  # Remplacé par ton ID Telegram
ADMIN_USERNAME = "deku225"
PRODUCTS_FILE = "products.json"
user_state = {}

# Charger les produits
def load_products():
    try:
        with open(PRODUCTS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

# Sauvegarder les produits
def save_products(products):
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(products, f, indent=2)

# Commande /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛍️ Bienvenue sur *Deku225-shop !*\n"
        "Voici les commandes disponibles :\n\n"
        "• /produits – Voir les produits\n"
        "• /avis – Lire les avis clients\n"
        "• /admin – Gérer la boutique (admin uniquement)\n",
        parse_mode="Markdown"
    )

# Commande /avis
async def avis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⭐ Avis des clients ⭐\n\n💬 Très bon service.\n💬 Livraison rapide.\n💬 Je recommande !")

# Commande /produits
async def produits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products = load_products()
    if not products:
        await update.message.reply_text("Aucun produit disponible.")
        return

    for p in products:
        promo_label = "🔥 Promo : " if p.get("promo") else ""
        message = f"*{promo_label}{p['title']}*\n💰 Prix : {p['price']} FCFA"
        button = InlineKeyboardButton("Commander", callback_data=f"buy_{p['title']}")
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup([[button]]),
            parse_mode="Markdown"
        )

# Bouton Commander
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("buy_"):
        product_name = query.data[4:]
        products = load_products()
        selected = next((p for p in products if p['title'] == product_name), None)

        if selected:
            user_state[query.from_user.id] = {"selected_product": selected}
            await query.message.reply_text(
                f"Deku225-shop:\n📝 Tu as choisi *{selected['title']}*.\n\n"
                "💵 Pour valider ta commande, effectue un dépôt sur l’un des numéros suivants :\n\n"
                "📱 Wave : +2250575719113\n"
                "📱 Orange Money : +2250718623773\n"
                "📱 MTN : +2250596430369\n\n"
                "Ensuite, envoie l'ID de ta transaction ici pour confirmer ton achat.",
                parse_mode="Markdown"
            )

# Réception ID transaction
async def handle_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_state or 'selected_product' not in user_state[user_id]:
        return

    product = user_state[user_id]['selected_product']
    transaction_id = update.message.text

    await update.message.reply_text(
        f"✅ Commande pour *{product['title']}* reçue avec l'ID : {transaction_id}.\n"
        f"⏳ En attente de validation par @{ADMIN_USERNAME}.",
        parse_mode="Markdown"
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"📥 Nouvelle commande reçue !\n\n"
            f"Produit : {product['title']}\n"
            f"ID Transaction : {transaction_id}\n"
            f"Client : @{update.message.from_user.username or update.message.from_user.id}"
        )
    )

# Commande /admin
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Accès refusé.")
        return

    await update.message.reply_text(
        "🎛️ Menu Admin :\n"
        "/add titre | prix – Ajouter\n"
        "/del titre – Supprimer\n"
        "/promo titre | on/off – Gérer promo\n"
        "/edit titre | nouveau titre | nouveau prix – Modifier\n"
        "/produits – Voir les produits"
    )

# Ajout d’un produit
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    try:
        text = update.message.text.split(" ", 1)[1]
        title, price = map(str.strip, text.split("|"))
        products = load_products()
        products.append({
            "title": title,
            "price": price,
            "promo": False,
            "promo_end": ""
        })
        save_products(products)
        await update.message.reply_text(f"✅ Produit ajouté : {title}")
    except:
        await update.message.reply_text("❌ Format : /add Titre | Prix")

# Suppression
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    try:
        title = update.message.text.split(" ", 1)[1].strip()
        products = load_products()
        products = [p for p in products if p["title"] != title]
        save_products(products)
        await update.message.reply_text(f"🗑️ Supprimé : {title}")
    except:
        await update.message.reply_text("❌ Format : /del Titre")

# Promo
async def promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    try:
        text = update.message.text.split(" ", 1)[1]
        title, status = map(str.strip, text.split("|"))
        products = load_products()
        for p in products:
            if p["title"] == title:
                p["promo"] = (status.lower() == "on")
                p["promo_end"] = datetime.now().strftime("%Y-%m-%d") if p["promo"] else ""
        save_products(products)
        await update.message.reply_text(f"🔥 Promo {'activée' if status=='on' else 'désactivée'} pour {title}")
    except:
        await update.message.reply_text("❌ Format : /promo Titre | on/off")

# Modification
async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    try:
        text = update.message.text.split(" ", 1)[1]
        old, new, price = map(str.strip, text.split("|"))
        products = load_products()
        for p in products:
            if p["title"] == old:
                p["title"] = new
                p["price"] = price
        save_products(products)
        await update.message.reply_text(f"✏️ Produit modifié : {new}")
    except:
        await update.message.reply_text("❌ Format : /edit Ancien titre | Nouveau titre | Nouveau prix")

# Lancement du bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("avis", avis))
    app.add_handler(CommandHandler("produits", produits))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("del", delete))
    app.add_handler(CommandHandler("promo", promo))
    app.add_handler(CommandHandler("edit", edit))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_transaction))
    print("Bot en cours d'exécution...")
    app.run_polling()
