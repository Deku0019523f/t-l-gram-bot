import os
import json
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    filters,
    ConversationHandler,
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))

PRODUCT_FILE = "products.json"
WAITING_FOR_TRANSACTION = {}

# Fonctions utilitaires
def load_products():
    if not os.path.exists(PRODUCT_FILE):
        return []
    with open(PRODUCT_FILE, "r") as f:
        return json.load(f)

def save_products(products):
    with open(PRODUCT_FILE, "w") as f:
        json.dump(products, f, indent=4)

# Commande /start
async def start(update: Update, context: CallbackContext):
    keyboard = [
        [KeyboardButton("/produits")],
        [KeyboardButton("/avis")],
        [KeyboardButton("/contact")],
        [KeyboardButton("/admin")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "🛍️ *Bienvenue sur Deku225-shop !*\nVoici les commandes disponibles :",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# Afficher les produits
async def produits(update: Update, context: CallbackContext):
    products = load_products()
    if not products:
        await update.message.reply_text("Aucun produit disponible.")
        return

    for p in products:
        promo_label = "🔥 Promo : " if p.get("promo") else ""
        message = f"*{promo_label}{p['title']}*\n💰 Prix : {p['price']} FCFA"
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🛒 Commander", callback_data=f"order_{p['title']}")]]
            )
        )

# Gérer les commandes via bouton
async def handle_order(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    product = query.data.split("_", 1)[1]
    WAITING_FOR_TRANSACTION[query.from_user.id] = product
    await query.message.reply_text(
        f"Deku225-shop:\n📝 Tu as choisi *{product}*.\n\n"
        "💵 Pour valider ta commande, effectue un dépôt sur l’un des numéros suivants :\n\n"
        "📱 Wave : +2250575719113\n"
        "📱 Orange Money : +2250718623773\n"
        "📱 MTN : +2250596430369\n\n"
        "Ensuite, envoie l'ID de ta transaction ici pour confirmer ton achat.",
        parse_mode="Markdown"
    )

# Traitement du message contenant un ID de transaction
async def handle_transaction(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    transaction_id = update.message.text.strip()

    if user_id in WAITING_FOR_TRANSACTION:
        product = WAITING_FOR_TRANSACTION.pop(user_id)

        await update.message.reply_text(
            f"✅ Commande pour *{product}* reçue avec l'ID : `{transaction_id}`.\n"
            f"⏳ En attente de validation par @deku225.",
            parse_mode="Markdown"
        )

        # Envoie à l'admin
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=(
                f"📥 Nouvelle commande de {update.effective_user.full_name} (@{update.effective_user.username or 'Non défini'})\n"
                f"📦 Produit : *{product}*\n"
                f"🧾 Transaction ID : `{transaction_id}`"
            ),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("Aucune commande en attente. Veuillez utiliser /produits pour recommencer.")

# Commande /contact
async def contact(update: Update, context: CallbackContext):
    await update.message.reply_text("Pour toute question, contactez : @deku225")

# Commande /avis
async def avis(update: Update, context: CallbackContext):
    await update.message.reply_text("⭐ Les clients adorent notre service rapide et fiable !")

# Menu admin
async def admin(update: Update, context: CallbackContext):
    if update.message.chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Accès refusé.")
        return

    await update.message.reply_text(
        "🛠️ Menu Admin :\n"
        "/ajouter titre | prix\n"
        "/supprimer titre\n"
        "/promo titre\n"
        "/modifprix titre | nouveau_prix\n"
        "/modiftitre ancien_titre | nouveau_titre"
    )

# Ajouter un produit
async def ajouter(update: Update, context: CallbackContext):
    if update.message.chat_id != ADMIN_CHAT_ID:
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
        await update.message.reply_text("Format invalide. Utilisez : /ajouter Titre | Prix")

# Supprimer un produit
async def supprimer(update: Update, context: CallbackContext):
    if update.message.chat_id != ADMIN_CHAT_ID:
        return
    try:
        title = update.message.text.split(" ", 1)[1].strip()
        products = load_products()
        products = [p for p in products if p["title"] != title]
        save_products(products)
        await update.message.reply_text(f"🗑️ Produit supprimé : {title}")
    except:
        await update.message.reply_text("Format invalide. Utilisez : /supprimer Titre")

# Activer promo
async def promo(update: Update, context: CallbackContext):
    if update.message.chat_id != ADMIN_CHAT_ID:
        return
    try:
        title = update.message.text.split(" ", 1)[1].strip()
        products = load_products()
        found = False
        for p in products:
            if p["title"] == title:
                p["promo"] = True
                p["promo_end"] = "fin juillet"
                found = True
        save_products(products)
        msg = "✅ Promo activée !" if found else "Produit non trouvé."
        await update.message.reply_text(msg)
    except:
        await update.message.reply_text("Format : /promo titre")

# Modifier prix
async def modifprix(update: Update, context: CallbackContext):
    if update.message.chat_id != ADMIN_CHAT_ID:
        return
    try:
        title, new_price = map(str.strip, update.message.text.split(" ", 1)[1].split("|"))
        products = load_products()
        for p in products:
            if p["title"] == title:
                p["price"] = new_price
        save_products(products)
        await update.message.reply_text(f"✅ Prix modifié pour {title}")
    except:
        await update.message.reply_text("Format : /modifprix titre | nouveau_prix")

# Modifier titre
async def modiftitre(update: Update, context: CallbackContext):
    if update.message.chat_id != ADMIN_CHAT_ID:
        return
    try:
        old_title, new_title = map(str.strip, update.message.text.split(" ", 1)[1].split("|"))
        products = load_products()
        for p in products:
            if p["title"] == old_title:
                p["title"] = new_title
        save_products(products)
        await update.message.reply_text(f"✏️ Titre modifié : {old_title} → {new_title}")
    except:
        await update.message.reply_text("Format : /modiftitre ancien_titre | nouveau_titre")

# Main
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("produits", produits))
    app.add_handler(CommandHandler("avis", avis))
    app.add_handler(CommandHandler("contact", contact))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("ajouter", ajouter))
    app.add_handler(CommandHandler("supprimer", supprimer))
    app.add_handler(CommandHandler("promo", promo))
    app.add_handler(CommandHandler("modifprix", modifprix))
    app.add_handler(CommandHandler("modiftitre", modiftitre))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_transaction))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, start))
    app.add_handler(MessageHandler(filters.ALL & filters.COMMAND, start))
    app.add_handler(MessageHandler(filters.ALL, handle_transaction))
    app.add_handler(MessageHandler(filters.TEXT, handle_transaction))
    app.add_handler(MessageHandler(filters.Regex("^/produits$"), produits))
    app.add_handler(MessageHandler(filters.Regex("^/avis$"), avis))
    app.add_handler(MessageHandler(filters.Regex("^/contact$"), contact))
    app.add_handler(MessageHandler(filters.Regex("^/admin$"), admin))
    app.add_handler(MessageHandler(filters.Regex("^/start$"), start))
    app.add_handler(MessageHandler(filters.Regex("^/start$"), start))
    app.add_handler(MessageHandler(filters.ALL, handle_transaction))
    app.add_handler(MessageHandler(filters.ALL, handle_transaction))
    app.add_handler(MessageHandler(filters.ALL, handle_transaction))
    app.add_handler(MessageHandler(filters.ALL, handle_transaction))
    app.add_handler(MessageHandler(filters.ALL, handle_transaction))
    app.add_handler(MessageHandler(filters.ALL, handle_transaction))
    app.add_handler(MessageHandler(filters.ALL, handle_transaction))
    app.add_handler(MessageHandler(filters.ALL, handle_transaction))
    app.add_handler(MessageHandler(filters.ALL, handle_transaction))

    app.add_handler(MessageHandler(filters.ALL, handle_transaction))
    app.add_handler(MessageHandler(filters.ALL, handle_transaction))

    app.add_handler(MessageHandler(filters.ALL, handle_transaction))

    app.add_handler(MessageHandler(filters.ALL, handle_transaction))

    app.add_handler(MessageHandler(filters.ALL, handle_transaction))

    app.add_handler(MessageHandler(filters.ALL, handle_transaction))

    app.add_handler(MessageHandler(filters.ALL, handle_transaction))
    app.add_handler(MessageHandler(filters.ALL, handle_transaction))
    app.add_handler(MessageHandler(filters.ALL, handle_transaction))

    app.add_handler(MessageHandler(filters.ALL, handle_transaction))
    app.add_handler(MessageHandler(filters.ALL, handle_transaction))

    app.add_handler(MessageHandler(filters.ALL, handle_transaction))
    app.add_handler(MessageHandler(filters.ALL, handle_transaction))

    app.add_handler(MessageHandler(filters.ALL, handle_transaction))
    app.add_handler(MessageHandler(filters.ALL, handle_transaction))

    app.add_handler(MessageHandler(filters.ALL, handle_transaction))

    app.add_handler(MessageHandler(filters.ALL, handle_transaction))

    app.add_handler(MessageHandler(filters.ALL, handle_transaction))

    app.add_handler(MessageHandler(filters.ALL, handle_transaction))

    app.add_handler(MessageHandler(filters.ALL, handle_transaction))

    app.add_handler(MessageHandler(filters.ALL, handle_transaction))

    app.add_handler(MessageHandler(filters.ALL, handle_transaction))

    app.add_handler(MessageHandler(filters.ALL, handle_transaction))

    app.add_handler(MessageHandler(filters.ALL, handle_transaction))

    app.add_handler(MessageHandler(filters.ALL, handle_transaction))

    app.add_handler(MessageHandler(filters.ALL, handle_transaction))
    
    app.add_handler(MessageHandler(filters.ALL, handle_transaction))

    app.run_polling()
