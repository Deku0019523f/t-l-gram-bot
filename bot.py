import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv

load_dotenv()

ADMIN_USERNAME = "deku225"
PRODUCTS_FILE = "products.json"

def load_products():
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_products(products):
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "🎉 Bienvenue sur Informatique Shop !\n\n"
        "📦 Produits : Abonnements internet, IPTV, Netflix, TikTok boost, etc.\n"
        "💳 Paiement : Orange Money / Moov / Wave\n"
        "✉️ Contact : @deku225\n\n"
        "Cliquez ci-dessous pour voir les produits, les avis et contacter un agent ⬇️"
    )
    keyboard = [
        [InlineKeyboardButton("🛒 Voir les produits", callback_data="products")],
        [InlineKeyboardButton("💬 Avis", callback_data="avis")],
        [InlineKeyboardButton("📞 Contacter un agent", url="https://t.me/deku225")]
    ]
    await update.message.reply_text(welcome_msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    products = load_products()
    messages = []
    for p in products:
        promo = p.get("promo", False)
        line = f"🔹 {p['title']}\n💵 {p['price']} FCFA"
        if promo:
            line = f"🔥 PROMO 🔥\n{line}\n⏳ Jusqu'au {p.get('promo_end', 'bientôt')}"
        messages.append(line)
    await query.message.reply_text("\n\n".join(messages))

async def show_avis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("⭐️ Merci de nous laisser un avis !\n👉 https://t.me/deku225")

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username != ADMIN_USERNAME:
        await update.message.reply_text("Accès refusé.")
        return

    keyboard = [
        [InlineKeyboardButton("📥 Ajouter Produit", callback_data="admin_add")],
        [InlineKeyboardButton("📝 Modifier Produit", callback_data="admin_modify")],
        [InlineKeyboardButton("🗑 Supprimer Produit", callback_data="admin_delete")],
        [InlineKeyboardButton("🔥 Gérer Promo", callback_data="admin_promo")],
    ]
    await update.message.reply_text("🛠 Menu Admin :", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_action"] = "add"
    await query.message.reply_text("Envoie :\n`Nom | Prix | Catégorie`", parse_mode="Markdown")

async def handle_modify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_action"] = "modify"
    products = load_products()
    text = "\n".join([f"{i+1}. {p['title']} ({p['price']} FCFA)" for i, p in enumerate(products)])
    await query.message.reply_text(f"Produits :\n{text}\n\nNuméro à modifier ?")

async def handle_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_action"] = "delete"
    products = load_products()
    text = "\n".join([f"{i+1}. {p['title']}" for i, p in enumerate(products)])
    await query.message.reply_text(f"Produits :\n{text}\n\nNuméro à supprimer ?")

async def handle_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_action"] = "promo"
    products = load_products()
    text = "\n".join([f"{i+1}. {p['title']} - Promo : {p.get('promo', False)}" for i, p in enumerate(products)])
    await query.message.reply_text(f"Produits :\n{text}\n\nEnvoie :\n`numéro | true/false | AAAA-MM-JJ`")

async def handle_admin_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username != ADMIN_USERNAME:
        return

    action = context.user_data.get("admin_action")
    text = update.message.text
    products = load_products()

    try:
        if action == "add":
            title, price, category = [x.strip() for x in text.split("|")]
            products.append({"title": title, "price": int(price), "category": category})
            save_products(products)
            await update.message.reply_text(f"✅ Ajouté : {title}")

        elif action == "modify":
            index = int(text.strip()) - 1
            context.user_data["modify_index"] = index
            context.user_data["admin_action"] = "confirm_modify"
            await update.message.reply_text("Nouveau format : `Nom | Prix | Catégorie`")

        elif action == "confirm_modify":
            title, price, category = [x.strip() for x in text.split("|")]
            index = context.user_data["modify_index"]
            products[index] = {"title": title, "price": int(price), "category": category}
            save_products(products)
            await update.message.reply_text("✅ Modifié.")

        elif action == "delete":
            index = int(text.strip()) - 1
            deleted = products.pop(index)
            save_products(products)
            await update.message.reply_text(f"🗑 Supprimé : {deleted['title']}")

        elif action == "promo":
            i, val, end = [x.strip() for x in text.split("|")]
            index = int(i) - 1
            products[index]["promo"] = val.lower() == "true"
            products[index]["promo_end"] = end
            save_products(products)
            await update.message.reply_text("🔥 Promo mise à jour.")

    except Exception as e:
        await update.message.reply_text(f"❌ Erreur : {e}")

if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(show_products, pattern="^products$"))
    app.add_handler(CallbackQueryHandler(show_avis, pattern="^avis$"))
    app.add_handler(CommandHandler("admin", admin_menu))
    app.add_handler(CallbackQueryHandler(handle_add, pattern="^admin_add$"))
    app.add_handler(CallbackQueryHandler(handle_modify, pattern="^admin_modify$"))
    app.add_handler(CallbackQueryHandler(handle_delete, pattern="^admin_delete$"))
    app.add_handler(CallbackQueryHandler(handle_promo, pattern="^admin_promo$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_response))
    app.run_polling()
    
