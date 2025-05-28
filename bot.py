import os 
import json 
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

ADMIN_USERNAME = "@deku225" PRODUCTS_FILE = "products.json" PAYMENT_NUMBERS = """\n💳 Numéros pour le paiement : • Wave : +2250575719113 • Orange : +2250718623773 • MTN : +2250596430369\n"""

Charger les produits depuis le fichier JSON

def load_products(): if not os.path.exists(PRODUCTS_FILE): return [] with open(PRODUCTS_FILE, "r") as f: return json.load(f)

Sauvegarder les produits dans le fichier JSON

def save_products(products): with open(PRODUCTS_FILE, "w") as f: json.dump(products, f, indent=2)

Formater l'affichage d'un produit

def format_product(prod, index): promo_tag = "🔥 Promo" if prod.get("promo") else "" return f"{index+1}. {prod['name']} - {prod['price']} FCFA {promo_tag}"

Commande /start

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): products = load_products() keyboard = [[InlineKeyboardButton("Commander", callback_data=f"order_{i}")] for i in range(len(products))] msg = "🛒 Nos produits disponibles :\n\n" msg += "\n".join(format_product(p, i) for i, p in enumerate(products)) await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

Bouton retour

async def retour(update: Update, context: ContextTypes.DEFAULT_TYPE): query = update.callback_query await query.answer() await start(update, context)

Gestion des commandes

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE): query = update.callback_query await query.answer() data = query.data if data.startswith("order_"): index = int(data.split("_")[1]) products = load_products() product = products[index] context.user_data['product'] = product msg = f"Vous avez choisi : {product['name']} - {product['price']} FCFA\n{PAYMENT_NUMBERS}\n\nVeuillez envoyer l'ID de la transaction après paiement." await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([ [InlineKeyboardButton("🔙 Retour", callback_data="retour")] ])) elif data == "retour": await retour(update, context)

Réception du reçu

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE): if 'product' in context.user_data: product = context.user_data['product'] receipt = f"🧾 Reçu de commande\n\nProduit : {product['name']}\nPrix : {product['price']} FCFA\n\nID de transaction : {update.message.text}\n\nMerci pour votre achat !" await update.message.reply_text(receipt, parse_mode="Markdown") del context.user_data['product']

Commande /avis

async def avis(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("💬 Pour laisser un avis, répondez simplement à ce message avec votre retour. Merci !")

ADMIN - Ajout produit

async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE): if update.message.from_user.username != ADMIN_USERNAME[1:]: return try: name, price = update.message.text.split(" ", 1)[1].rsplit(" ", 1) products = load_products() products.append({"name": name, "price": price, "promo": False}) save_products(products) await update.message.reply_text("✅ Produit ajouté.") except: await update.message.reply_text("Utilise : /add Nom_du_produit Prix")

ADMIN - Supprimer produit

async def del_product(update: Update, context: ContextTypes.DEFAULT_TYPE): if update.message.from_user.username != ADMIN_USERNAME[1:]: return try: index = int(update.message.text.split(" ", 1)[1]) - 1 products = load_products() removed = products.pop(index) save_products(products) await update.message.reply_text(f"🗑️ Supprimé : {removed['name']}") except: await update.message.reply_text("Utilise : /del numéro_du_produit")

ADMIN - Activer promo

async def promo_product(update: Update, context: ContextTypes.DEFAULT_TYPE): if update.message.from_user.username != ADMIN_USERNAME[1:]: return try: index = int(update.message.text.split(" ", 1)[1]) - 1 products = load_products() products[index]["promo"] = True save_products(products) await update.message.reply_text(f"🔥 Promo activée pour : {products[index]['name']}") except: await update.message.reply_text("Utilise : /promo numéro_du_produit")

Lancer le bot

if name == 'main': TOKEN = os.getenv("BOT_TOKEN") app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("avis", avis))
app.add_handler(CommandHandler("add", add_product))
app.add_handler(CommandHandler("del", del_product))
app.add_handler(CommandHandler("promo", promo_product))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("✅ Bot en ligne !")
app.run_polling()

