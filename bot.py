import json import datetime from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

=== CONFIGURATION ===

TOKEN = "TON_TOKEN_ICI" ADMIN_USERNAME = "deku225" PRODUCTS_FILE = "products.json"

=== FONCTIONS UTILITAIRES ===

def load_products(): with open(PRODUCTS_FILE, "r") as f: return json.load(f)

def save_products(products): with open(PRODUCTS_FILE, "w") as f: json.dump(products, f, indent=2)

=== MENU ADMIN ===

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE): user = update.effective_user if user.username != ADMIN_USERNAME: await update.message.reply_text("⛔ Accès refusé.") return

keyboard = [
    [InlineKeyboardButton("📤 Ajouter un produit", callback_data="admin_add")],
    [InlineKeyboardButton("✏️ Modifier un produit", callback_data="admin_edit")],
    [InlineKeyboardButton("🗑️ Supprimer un produit", callback_data="admin_delete")],
    [InlineKeyboardButton("🔥 Activer/Désactiver promo", callback_data="admin_promo")]
]
reply_markup = InlineKeyboardMarkup(keyboard)
await update.message.reply_text("🛠️ Menu Admin:", reply_markup=reply_markup)

=== HANDLER DE CALLBACK ===

async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE): query = update.callback_query await query.answer() action = query.data

if action == "admin_add":
    await query.message.reply_text("Envoyez les infos du produit au format :\n`Nom | Prix | Catégorie`", parse_mode="Markdown")
    context.user_data["admin_action"] = "add"

elif action == "admin_edit":
    products = load_products()
    msg = "✏️ *Produits existants :*\n"
    for idx, p in enumerate(products):
        msg += f"{idx}. {p['title']} - {p['price']} FCFA\n"
    msg += "\nEnvoyez l'index + nouvelle info au format :\n`index | Nom | Prix | Catégorie`"
    await query.message.reply_text(msg, parse_mode="Markdown")
    context.user_data["admin_action"] = "edit"

elif action == "admin_delete":
    products = load_products()
    msg = "🗑️ *Produits disponibles :*\n"
    for idx, p in enumerate(products):
        msg += f"{idx}. {p['title']} - {p['price']} FCFA\n"
    msg += "\nEnvoyez simplement l'index du produit à supprimer."
    await query.message.reply_text(msg, parse_mode="Markdown")
    context.user_data["admin_action"] = "delete"

elif action == "admin_promo":
    products = load_products()
    msg = "🔥 *Produits pour activer/désactiver une promo :*\n"
    for idx, p in enumerate(products):
        promo = "✅" if p.get("promo") else "❌"
        msg += f"{idx}. {p['title']} - Promo: {promo}\n"
    msg += "\nEnvoyez au format :\n`index | true/false | YYYY-MM-DD (optionnel)`"
    await query.message.reply_text(msg, parse_mode="Markdown")
    context.user_data["admin_action"] = "promo"

=== TRAITEMENT DES RÉPONSES TEXTE ===

async def handle_admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE): if update.effective_user.username != ADMIN_USERNAME: return

action = context.user_data.get("admin_action")
text = update.message.text
products = load_products()

try:
    if action == "add":
        nom, prix, cat = [x.strip() for x in text.split("|")]
        products.append({"title": nom, "price": int(prix), "category": cat})
        save_products(products)
        await update.message.reply_text("✅ Produit ajouté !")

    elif action == "edit":
        idx, nom, prix, cat = [x.strip() for x in text.split("|")]
        products[int(idx)] = {"title": nom, "price": int(prix), "category": cat}
        save_products(products)
        await update.message.reply_text("✏️ Produit modifié.")

    elif action == "delete":
        idx = int(text.strip())
        deleted = products.pop(idx)
        save_products(products)
        await update.message.reply_text(f"🗑️ Produit supprimé: {deleted['title']}")

    elif action == "promo":
        parts = [x.strip() for x in text.split("|")]
        if len(parts) < 2:
            await update.message.reply_text("⛔ Format invalide. Essayez : `index | true/false | date`", parse_mode="Markdown")
            return
        idx = int(parts[0])
        status = parts[1].lower() == "true"
        end_date = parts[2] if len(parts) == 3 else None
        products[idx]["promo"] = status
        products[idx]["promo_end"] = end_date
        save_products(products)
        await update.message.reply_text("🔥 Promo mise à jour.")

    context.user_data["admin_action"] = None

except Exception as e:
    await update.message.reply_text(f"⚠️ Erreur : {e}")

=== DÉMARRAGE BOT ===

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("admin", admin_menu)) app.add_handler(CallbackQueryHandler(handle_admin_action, pattern="^admin_")) app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_text))

print("🤖 Bot admin prêt !") app.run_polling()

