import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# Identifiant Telegram de l'administrateur
ADMIN_USERNAME = "deku225"

# Charger les produits
def load_products():
    with open("products.json", "r") as f:
        return json.load(f)

# Sauvegarder les produits
def save_products(products):
    with open("products.json", "w") as f:
        json.dump(products, f, indent=2)

# Générer les boutons pour les produits
def generate_product_buttons(products):
    buttons = []
    for index, product in enumerate(products):
        label = f"🔥 Promo - {product['title']}" if product.get("promo") else product['title']
        buttons.append([InlineKeyboardButton(label, callback_data=f"product_{index}")])
    return buttons

# Page d'accueil
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🛍️ *Bienvenue sur la boutique !*\n"
        "Sélectionnez un produit ci-dessous pour commander.\n\n"
        "_Vous pouvez payer via :_\n"
        "📱 MTN : +2250596430369\n"
        "📱 ORANGE : +2250718623773\n"
        "📱 WAVE : +2250575719113\n\n"
        "🛒 Commandez facilement et rapidement !"
    )
    products = load_products()
    reply_markup = InlineKeyboardMarkup(generate_product_buttons(products))
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

# Commande /avis
async def avis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🙏 Merci de laisser un avis ! Tapez votre avis ici, nous le lirons avec attention.")

# Affichage d’un produit
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("product_"):
        index = int(data.split("_")[1])
        product = load_products()[index]
        text = (
            f"📦 *{product['title']}*\n"
            f"💰 Prix : {product['price']} FCFA\n"
            f"📂 Catégorie : {product['category']}\n\n"
            "👉 Cliquez sur 'Commander' pour poursuivre."
        )
        keyboard = [
            [InlineKeyboardButton("✅ Commander", callback_data=f"order_{index}")],
            [InlineKeyboardButton("⬅️ Retour", callback_data="home")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("order_"):
        index = int(data.split("_")[1])
        context.user_data["order_index"] = index
        await query.edit_message_text(
            "🔁 Envoyez l'identifiant de transaction et le moyen de paiement (ex: *WAVE 123456789*)",
            parse_mode="Markdown"
        )

    elif data == "home":
        products = load_products()
        await query.edit_message_text(
            "🛍️ *Retour à la boutique*\n\n_Sélectionnez un produit ci-dessous_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(generate_product_buttons(products))
        )

# Gestion du reçu après transaction
async def handle_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "order_index" not in context.user_data:
        return

    index = context.user_data["order_index"]
    product = load_products()[index]
    msg = update.message.text

    receipt = (
        f"🧾 *Reçu de commande*\n"
        f"📦 Produit : {product['title']}\n"
        f"💳 Paiement : {msg}\n"
        f"💰 Prix : {product['price']} FCFA\n"
        f"👤 Client : @{update.effective_user.username or update.effective_user.first_name}\n\n"
        f"Merci d’avoir commandé !"
    )
    await update.message.reply_text(receipt, parse_mode="Markdown")
    del context.user_data["order_index"]

# ADMIN : Ajouter un produit
async def admin_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != ADMIN_USERNAME:
        return
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Usage : /add Titre Prix Catégorie")
        return
    title = args[0]
    price = int(args[1])
    category = args[2]
    products = load_products()
    products.append({"title": title, "price": price, "category": category})
    save_products(products)
    await update.message.reply_text(f"✅ Produit '{title}' ajouté.")

# ADMIN : Supprimer un produit
async def admin_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != ADMIN_USERNAME:
        return
    args = context.args
    if not args:
        await update.message.reply_text("Usage : /del IndexProduit")
        return
    index = int(args[0])
    products = load_products()
    if 0 <= index < len(products):
        removed = products.pop(index)
        save_products(products)
        await update.message.reply_text(f"❌ Produit supprimé : {removed['title']}")
    else:
        await update.message.reply_text("❌ Index invalide.")

# ADMIN : Mettre un produit en promo
async def admin_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != ADMIN_USERNAME:
        return
    args = context.args
    if not args:
        await update.message.reply_text("Usage : /promo IndexProduit")
        return
    index = int(args[0])
    products = load_products()
    if 0 <= index < len(products):
        products[index]["promo"] = True
        save_products(products)
        await update.message.reply_text(f"🔥 Produit mis en promo : {products[index]['title']}")
    else:
        await update.message.reply_text("❌ Index invalide.")

# Lancer le bot
if __name__ == "__main__":
    app = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("avis", avis))
    app.add_handler(CommandHandler("add", admin_add))
    app.add_handler(CommandHandler("del", admin_del))
    app.add_handler(CommandHandler("promo", admin_promo))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_transaction))

    print("✅ Bot en ligne !")
    app.run_polling()
