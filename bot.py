import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext

TOKEN = 'TON_TOKEN_ICI'
ADMIN_USERNAME = 'deku225'

# Numéros de paiement
PAYMENT_NUMBERS = {
    "Orange": "+2250718623773",
    "MTN": "+2250596430369",
    "Wave": "+2250575719113"
}

# Chargement des produits
def load_products():
    with open('products.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_products(products):
    with open('products.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

products = load_products()

def is_promo_active(product):
    if not product.get("promo"):
        return False
    try:
        promo_end = datetime.strptime(product["promo_end"], "%Y-%m-%d")
        return datetime.now() <= promo_end
    except Exception:
        return False

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    username = user.username or user.first_name

    welcome_msg = (
        f"👋 Bonjour @{username} !\n\n"
        "Bienvenue sur le bot de commande. Voici nos produits disponibles :\n\n"
    )
    keyboard = []
    for prod in products:
        label = prod["title"]
        if is_promo_active(prod):
            label += " 🔥 Promo"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"commande_{prod['title']}")])
    keyboard.append([InlineKeyboardButton("🛒 Avis", callback_data="avis")])
    keyboard.append([InlineKeyboardButton("📞 Contacter un agent", callback_data="contact_agent")])

    description = (
        "\n\nℹ️ *Description du bot* :\n"
        "Ce bot vous permet de commander facilement des abonnements, logiciels et services. "
        "Après avoir choisi un produit, vous recevrez les instructions de paiement.\n\n"
        "Pour toute question, utilisez le bouton *Contacter un agent*."
    )

    update.message.reply_text(
        welcome_msg + description,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data

    if data.startswith("commande_"):
        title = data.split("commande_")[1]
        product = next((p for p in products if p["title"] == title), None)
        if not product:
            query.edit_message_text("Produit introuvable.")
            return

        price = product["price"]
        if is_promo_active(product):
            price = product["price"]  # Le prix déjà promo dans JSON

        pay_msg = (
            f"🛒 *Commande :* {title}\n"
            f"💰 Prix : {price} FCFA\n\n"
            "💳 *Mode de paiement :*\n"
            "Envoyez-moi le numéro de la transaction ainsi que le moyen choisi (exemple : `TX12345678 Orange`)\n\n"
            "📞 *Numéros disponibles :*\n"
        )
        for key, num in PAYMENT_NUMBERS.items():
            pay_msg += f"• {key} : {num}\n"

        pay_msg += "\n⬅️ Appuyez sur Retour pour revenir à la liste."

        keyboard = [
            [InlineKeyboardButton("⬅️ Retour", callback_data="retour")]
        ]

        query.edit_message_text(pay_msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        context.user_data["pending_order"] = title

    elif data == "retour":
        # Retour à la liste produits
        keyboard = []
        for prod in products:
            label = prod["title"]
            if is_promo_active(prod):
                label += " 🔥 Promo"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"commande_{prod['title']}")])
        keyboard.append([InlineKeyboardButton("🛒 Avis", callback_data="avis")])
        keyboard.append([InlineKeyboardButton("📞 Contacter un agent", callback_data="contact_agent")])
        query.edit_message_text(
            "Voici la liste des produits disponibles :",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data == "avis":
        query.edit_message_text(
            "📢 *Avis des clients* :\n\n"
            "Merci pour votre confiance ! Envoyez-nous votre avis ou utilisez le bouton Contacter un agent pour toute question.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Retour", callback_data="retour")]
            ])
        )

    elif data == "contact_agent":
        query.edit_message_text(
            "☎️ Vous pouvez contacter un agent ici : @deku225\n\n"
            "Merci de votre confiance !",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Retour", callback_data="retour")]
            ])
        )

def handle_transaction(update: Update, context: CallbackContext):
    user = update.effective_user
    username = user.username or user.first_name
    text = update.message.text.strip()

    if "pending_order" not in context.user_data:
        update.message.reply_text(
            "⚠️ Vous n'avez pas de commande en cours. Utilisez /start pour voir les produits."
        )
        return

    pending_title = context.user_data["pending_order"]
    product = next((p for p in products if p["title"] == pending_title), None)
    if not product:
        update.message.reply_text("⚠️ Produit non trouvé. Veuillez recommencer.")
        return

    # Exemple de validation simple: on attend un TX + moyen de paiement
    parts = text.split()
    if len(parts) < 2:
        update.message.reply_text(
            "⚠️ Format invalide. Envoyez le numéro de transaction suivi du moyen de paiement, ex: TX12345678 Orange"
        )
        return

    tx_number = parts[0]
    pay_method = parts[1].capitalize()

    if pay_method not in PAYMENT_NUMBERS:
        update.message.reply_text(
            "⚠️ Moyen de paiement inconnu. Choisissez parmi : Orange, MTN, Wave."
        )
        return

    price = product["price"]
    if is_promo_active(product):
        price = product["price"]

    # Envoi du reçu au client
    receipt = (
        f"✅ *Commande reçue*\n\n"
        f"Produit : {pending_title}\n"
        f"Prix : {price} FCFA\n"
        f"Transaction : {tx_number}\n"
