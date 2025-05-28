import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    CallbackQueryHandler, ContextTypes
)
from datetime import datetime

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_USERNAME = "@deku225"
PRODUCTS_FILE = "products.json"
pending_avis = {}

def load_products():
    try:
        with open(PRODUCTS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_products(products):
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(products, f, indent=2)

def format_product(product, index):
    promo_text = ""
    if "promo_price" in product and "promo_until" in product:
        try:
            if datetime.strptime(product["promo_until"], "%Y-%m-%d") >= datetime.today():
                promo_text = f"\n🔥 Promo : {product['promo_price']} FCFA jusqu’au {product['promo_until']}"
            else:
                promo_text = ""
        except:
            pass
    return f"📦 *{product['title']}*\n💰 Prix : {product['price']} FCFA{promo_text}\n🆔 ID : `{index+1}`"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🛒 Voir les produits", callback_data="show_products")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = (
        "🎉 *Bienvenue sur Informatique Shop !*\n\n"
        "📦 Produits : Abonnements internet, IPTV, Netflix, TikTok boost, etc.\n"
        "💳 Paiement : Orange Money / Moov / Wave\n"
        "✉️ Contact : @deku225\n"
        "\nCliquez ci-dessous pour voir les produits ⬇️"
    )
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    products = load_products()
    for i, product in enumerate(products):
        text = format_product(product, i)
        keyboard = [[InlineKeyboardButton("🛍️ Commander", callback_data=f"order_{i}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    await query.message.reply_text("⬅️ /cancel pour revenir au menu.")

async def order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    index = int(query.data.split("_")[1])
    products = load_products()
    if index >= len(products):
        await query.message.reply_text("Produit introuvable.")
        return
    product = products[index]
    await query.message.reply_text(
        f"🛒 Vous avez choisi : *{product['title']}*\n"
        f"💳 Prix : {product.get('promo_price', product['price'])} FCFA\n\n"
        f"Envoyez maintenant l'ID de votre transaction de paiement avec le moyen utilisé.",
        parse_mode="Markdown"
    )
    context.user_data["current_product"] = product

async def receive_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product = context.user_data.get("current_product")
    if not product:
        await update.message.reply_text("❌ Veuillez d’abord sélectionner un produit.")
        return
    transaction = update.message.text.strip()
    payment_methods = ["Orange Money", "Moov", "Wave"]
    method = "Non spécifié"
    for m in payment_methods:
        if m.lower() in transaction.lower():
            method = m
            break
    receipt = (
        "✅ *Commande reçue !*\n\n"
        f"📦 Produit : *{product['title']}*\n"
        f"💳 Paiement : *{method}*\n"
        f"🧾 ID Transaction : `{transaction}`\n\n"
        "Merci de patienter pendant la vérification."
    )
    await update.message.reply_text(receipt, parse_mode="Markdown")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Opération annulée. Retour au menu principal.")

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(update, context)

# === Avis ===
async def avis_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending_avis[update.effective_user.id] = True
    await update.message.reply_text("✍️ Envoyez maintenant votre avis :")

async def handle_avis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if pending_avis.get(user_id):
        avis_text = update.message.text.strip()
        del pending_avis[user_id]
        await update.message.reply_text("🙏 Merci pour votre avis !")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"🗣️ *Avis reçu :*\n_{avis_text}_", parse_mode="Markdown")

# === Admin ===
def is_admin(username):
    return username == ADMIN_USERNAME

async def admin_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.username):
        return
    products = load_products()
    text = "🛠️ *Produits enregistrés :*\n\n"
    for i, p in enumerate(products):
        text += f"{i+1}. {p['title']} - {p['price']} FCFA\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def admin_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.username):
        return
    args = update.message.text.replace("/add", "").strip()
    parts = args.split("|")
    if len(parts) != 2:
        await update.message.reply_text("Format invalide. Utilisez : /add titre|prix")
        return
    title, price = parts
    products = load_products()
    products.append({"title": title.strip(), "price": int(price)})
    save_products(products)
    await update.message.reply_text(f"Produit ajouté : {title} - {price} FCFA")

async def admin_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.username):
        return
    args = update.message.text.replace("/remove", "").strip()
    try:
        index = int(args) - 1
    except:
        await update.message.reply_text("Format : /remove <index>")
        return
    products = load_products()
    if 0 <= index < len(products):
        removed = products.pop(index)
        save_products(products)
        await update.message.reply_text(f"Produit supprimé : {removed['title']}")
    else:
        await update.message.reply_text("Index invalide.")

async def admin_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.username):
        return
    args = update.message.text.replace("/promo", "").strip()
    parts = args.split("|")
    if len(parts) != 3:
        await update.message.reply_text("Format invalide. Usage: /promo <index>|<new_price>|<yyyy-mm-dd>")
        return
    try:
        index = int(parts[0]) - 1
        new_price = int(parts[1])
        promo_until = parts[2].strip()
    except:
        await update.message.reply_text("Erreur de saisie. Vérifiez les données.")
        return
    products = load_products()
    if index < 0 or index >= len(products):
        await update.message.reply_text("Index invalide.")
        return
    products[index]["promo_price"] = new_price
    products[index]["promo_until"] = promo_until
    save_products(products)
    await update.message.reply_text(f"Promo activée pour '{products[index]['title']}' jusqu'au {promo_until}.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(show_products, pattern="show_products"))
    app.add_handler(CallbackQueryHandler(back, pattern="back"))
    app.add_handler(CallbackQueryHandler(order, pattern=r"order_\d+"))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_transaction))
    app.add_handler(CommandHandler("avis", avis_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_avis))

    # Admin
    app.add_handler(CommandHandler("admin", admin_products))
    app.add_handler(CommandHandler("add", admin_add))
    app.add_handler(CommandHandler("remove", admin_remove))
    app.add_handler(CommandHandler("promo", admin_promo))

    print("Bot en cours d'exécution...")
    app.run_polling()

if __name__ == "__main__":
    main()
