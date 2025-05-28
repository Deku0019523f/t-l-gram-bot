import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes,
)

# --- CONFIG ---
TOKEN = os.getenv("BOT_TOKEN")  # à configurer dans Railway

ADMIN_USERNAME = "deku225"

PAYMENT_NUMBERS = {
    "Wave": "+2250575719113",
    "Orange": "+2250718623773",
    "MTN": "+2250596430369"
}

PRODUCTS_FILE = "products.json"

# --- Fonctions utilitaires ---

def load_products():
    if not os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, "w") as f:
            json.dump([], f)
    with open(PRODUCTS_FILE, "r") as f:
        return json.load(f)

def save_products(products):
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

def format_product(product):
    title = product["title"]
    price = product["price"]
    promo_price = product.get("promo_price")
    promo_until = product.get("promo_until")
    now = None
    from datetime import datetime
    now = datetime.now().date()
    promo_active = False
    if promo_price and promo_until:
        try:
            promo_date = datetime.strptime(promo_until, "%Y-%m-%d").date()
            promo_active = promo_date >= now
        except Exception:
            promo_active = False
    if promo_active:
        return f"{title} - ~{price} FCFA~ **🔥 {promo_price} FCFA (Promo jusqu'au {promo_until})**"
    else:
        return f"{title} - {price} FCFA"

def is_admin(update: Update):
    user = update.effective_user
    return user and user.username == ADMIN_USERNAME

# --- Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Voir les produits", callback_data="show_products")],
        [InlineKeyboardButton("Avis", callback_data="avis")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Bienvenue dans la boutique. Choisissez une option :", reply_markup=reply_markup
    )

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    products = load_products()
    text = "Liste des produits :\n\n"
    buttons = []
    for i, p in enumerate(products):
        text += f"{i+1}. {format_product(p)}\n"
        buttons.append([InlineKeyboardButton(f"Commander {i+1}", callback_data=f"order_{i}")])
    buttons.append([InlineKeyboardButton("Retour", callback_data="back")])
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(buttons))

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(update, context)

async def order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    index = int(data.split("_")[1])
    products = load_products()
    if index < 0 or index >= len(products):
        await query.edit_message_text("Produit invalide.")
        return
    product = products[index]
    text = (
        f"Vous avez choisi : {format_product(product)}\n\n"
        "Envoyez maintenant votre numéro de transaction et le moyen de paiement utilisé (Wave, Orange, MTN).\n"
        "Exemple : 123456789 Wave\n"
        "Ou tapez /cancel pour annuler."
    )
    context.user_data["order_index"] = index
    await query.edit_message_text(text=text)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("order_index", None)
    await update.message.reply_text("Commande annulée.")

async def receive_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "order_index" not in context.user_data:
        await update.message.reply_text("Vous n'avez pas commencé une commande. Tapez /start.")
        return
    order_index = context.user_data["order_index"]
    products = load_products()
    product = products[order_index]
    text = update.message.text.strip()
    # On attend: "numéro moyen"
    parts = text.split()
    if len(parts) < 2:
        await update.message.reply_text(
            "Format invalide. Envoyez : <numéro transaction> <moyen de paiement (Wave, Orange, MTN)>."
        )
        return
    transaction_id = parts[0]
    payment_method = parts[1].capitalize()
    if payment_method not in PAYMENT_NUMBERS:
        await update.message.reply_text("Moyen de paiement invalide. Choisissez Wave, Orange ou MTN.")
        return
    # Générer reçu
    receipt = (
        f"📁 Fichier : {product['title']}\n"
        f"💰 Prix : {product.get('promo_price', product['price'])} FCFA\n"
        f"🔢 ID Transaction : {transaction_id}\n"
        f"📞 Moyen de paiement : {payment_method}\n"
        f"📞 Numéro pour confirmation : {PAYMENT_NUMBERS[payment_method]}\n\n"
        "Merci pour votre achat ! 🤖"
    )
    await update.message.reply_text(receipt)
    context.user_data.pop("order_index", None)

async def avis_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Pour laisser un avis, envoyez votre message ici. Nous vous remercions de votre retour."
    )

async def handle_avis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    # Ici, on pourrait enregistrer l'avis, envoyer à un admin, etc.
    # Pour l'instant on confirme la réception.
    await update.message.reply_text(f"Merci pour votre avis, {user.first_name} !")

# Admin commands
async def admin_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("Accès refusé.")
        return
    products = load_products()
    text = "Liste produits (admin):\n"
    for i, p in enumerate(products):
        text += f"{i+1}. {format_product(p)}\n"
    text += "\nUtilisez les commandes:\n"
    text += "/add <title>|<price>|<category>\n"
    text += "/remove <index>\n"
    text += "/promo <index>|<new_price>|<yyyy-mm-dd>\n"
    await update.message.reply_text(text)

async def admin_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("Accès refusé.")
        return
    args = update.message.text.split(' ', 1)
    if len(args) < 2:
        await update.message.reply_text("Usage: /add <title>|<price>|<category>")
        return
    parts = args[1].split("|")
    if len(parts) != 3:
        await update.message.reply_text("Format invalide. Usage: /add <title>|<price>|<category>")
        return
    title, price, category = parts
    try:
        price = int(price)
    except:
        await update.message.reply_text("Le prix doit être un nombre entier.")
        return
    products = load_products()
    products.append({"title": title.strip(), "price": price, "category": category.strip()})
    save_products(products)
    await update.message.reply_text(f"Produit '{title}' ajouté.")

async def admin_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("Accès refusé.")
        return
    args = update.message.text.split(' ', 1)
    if len(args) < 2:
        await update.message.reply_text("Usage: /remove <index>")
        return
    try:
        index = int(args[1]) - 1
    except:
        await update.message.reply_text("Index invalide.")
        return
    products = load_products()
    if index < 0 or index >= len(products):
        await update.message.reply_text("Index hors limite.")
        return
    removed = products.pop(index)
    save_products(products)
    await update.message.reply_text(f"Produit '{removed['title']}' supprimé.")

async def admin_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("Accès refusé.")
        return
    args = update.message.text.split(' ', 1)
    if len(args) < 2:
        await update.message.reply_text("Usage: /promo <index>|<new_price>|<yyyy-mm-dd>")
        return
    parts = args[1].split("|")
    if len(parts) != 3:
