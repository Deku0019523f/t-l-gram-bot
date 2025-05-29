import os
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, CallbackQueryHandler
)
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "1299831974"))

PRODUCTS_FILE = "products.json"

# Charger les produits
def load_products():
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_products(products):
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

# Commande /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛍️ Produits", callback_data='show_products')],
        [InlineKeyboardButton("⭐ Avis", callback_data='show_reviews')],
        [InlineKeyboardButton("⚙️ Admin", callback_data='admin')],
        [InlineKeyboardButton("📞 Contact", callback_data='contact')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        "🛍️ Bienvenue sur Deku225-shop !\n\n"
        "Voici les commandes disponibles :\n\n"
        "• /produits – Voir les produits\n"
        "• /avis – Lire les avis clients\n"
        "• /admin – Gérer la boutique (admin uniquement)\n"
        "• /contact - Contacter un agent\n"
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# Gestion des boutons
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'show_products':
        products = load_products()
        messages = []
        for idx, p in enumerate(products, start=1):
            promo_label = "🔥 Promo - " if p.get("promo") and p.get("promo_end") >= datetime.now().strftime("%Y-%m-%d") else ""
            msg = f"{idx}. *{promo_label}{p['title']}*\n💰 Prix : {p['price']} FCFA"
            messages.append(msg)
        text = "\n\n".join(messages)
        text += "\n\nPour commander un produit, tapez /commander <numéro du produit>"
        await query.message.reply_text(text, parse_mode="Markdown")

    elif query.data == 'show_reviews':
        # Ajouter ici les avis (exemple)
        await query.message.reply_text("📢 Avis clients:\n- Très bon service!\n- Livraison rapide.")

    elif query.data == 'admin':
        user_id = query.from_user.id
        if user_id != ADMIN_ID:
            await query.message.reply_text("❌ Accès refusé.")
            return
        await query.message.reply_text("⚙️ Menu Admin:\n- /ajouter\n- /modifier\n- /supprimer")

    elif query.data == 'contact':
        await query.message.reply_text("📞 Contactez @deku225 pour toute question.")

# Commander un produit
async def commander(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        idx = int(context.args[0]) - 1
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /commander <numéro du produit>")
        return

    products = load_products()
    if idx < 0 or idx >= len(products):
        await update.message.reply_text("Produit non trouvé.")
        return

    product = products[idx]['title']

    deposit_numbers = (
        "📱 Wave : +2250575719113\n"
        "📱 Orange Money : +2250718623773\n"
        "📱 MTN : +2250596430369"
    )

    msg = (
        f"📝 Tu as choisi *{product}*.\n\n"
        f"💵 Pour valider ta commande, effectue un dépôt sur l’un des numéros suivants :\n\n"
        f"{deposit_numbers}\n\n"
        "Ensuite, envoie l'ID de ta transaction ici pour confirmer ton achat."
    )

    # Enregistre la commande dans le contexte utilisateur
    context.user_data['pending_order'] = product

    await update.message.reply_text(msg, parse_mode="Markdown")

# Réception de l'ID de transaction
async def transaction_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if 'pending_order' not in context.user_data:
        await update.message.reply_text("Tu n'as pas de commande en attente. Utilise /commander pour passer une commande.")
        return

    product = context.user_data['pending_order']
    transaction_id = text

    # Envoyer la confirmation à l'admin
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"📥 Nouvelle commande de {update.effective_user.full_name} (@{update.effective_user.username}):\n"
            f"Produit : *{product}*\n"
            f"Transaction ID : `{transaction_id}`"
        ),
        parse_mode="Markdown"
    )

    await update.message.reply_text(
        f"✅ Commande pour *{product}* reçue avec l'ID : {transaction_id}.\n"
        f"⏳ En attente de validation par @deku225.",
        parse_mode="Markdown"
    )

    # Nettoyer la commande en attente
    del context.user_data['pending_order']

# Vérification admin /admin
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Accès refusé.")
        return

    await update.message.reply_text(
        "⚙️ Menu Admin:\n"
        "- /ajouter <titre> | <prix> | <catégorie>\n"
        "- /modifier <numéro> | <titre> | <prix> | <catégorie>\n"
        "- /supprimer <numéro>"
    )

# Ajouter produit
async def ajouter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Accès refusé.")
        return
    try:
        args_text = " ".join(context.args)
        title, price, category = [s.strip() for s in args_text.split("|")]
        price = int(price)
    except Exception:
        await update.message.reply_text("Usage: /ajouter <titre> | <prix> | <catégorie>")
        return

    products = load_products()
    products.append({"title": title, "price": price, "category": category})
    save_products(products)
    await update.message.reply_text(f"Produit ajouté : {title}")

# Modifier produit
async def modifier(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Accès refusé.")
        return
    try:
        args_text = " ".join(context.args)
        num_str, title, price, category = [s.strip() for s in args_text.split("|")]
        idx = int(num_str) - 1
        price = int(price)
    except Exception:
        await update.message.reply_text("Usage: /modifier <numéro> | <titre> | <prix> | <catégorie>")
        return

    products = load_products()
    if idx < 0 or idx >= len(products):
        await update.message.reply_text("Numéro de produit invalide.")
        return

    products[idx] = {"title": title, "price": price, "category": category}
    save_products(products)
    await update.message.reply_text(f"Produit modifié : {title}")

# Supprimer produit
async def supprimer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Accès refusé.")
        return
    try:
        idx = int(context.args[0]) - 1
    except Exception:
        await update.message.reply_text("Usage: /supprimer <numéro>")
        return

    products = load_products()
    if idx < 0 or idx >= len(products):
        await update.message.reply_text("Numéro de produit invalide.")
        return

    removed = products.pop(idx)
    save_products(products)
    await update.message.reply_text(f"Produit supprimé : {removed['title']}")

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(CommandHandler("produits", button_handler, filters=None, block=False))  # Optionnel
    application.add_handler(CommandHandler("commander", commander))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("ajouter", ajouter))
    application.add_handler(CommandHandler("modifier", modifier))
    application.add_handler(CommandHandler("supprimer", supprimer))

    # Gestion des messages texte pour ID transaction
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, transaction_id_handler))

    application.run_polling()

if __name__ == "__main__":
    main()
