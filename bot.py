import json import os from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

Fichier produits

PRODUCTS_FILE = 'products.json' ADMIN_USERNAME = '@deku225'

Chargement produits

def load_products(): if not os.path.exists(PRODUCTS_FILE): return [] with open(PRODUCTS_FILE, 'r') as f: return json.load(f)

def save_products(products): with open(PRODUCTS_FILE, 'w') as f: json.dump(products, f, indent=2)

Commande /start

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): user = update.effective_user keyboard = [[InlineKeyboardButton("Voir les produits", callback_data='list')]] await update.message.reply_text( f"Bienvenue dans la boutique, {user.first_name} !\n\n📦 Commandez facilement vos services numériques.\nCliquez ci-dessous pour commencer.", reply_markup=InlineKeyboardMarkup(keyboard) )

Afficher produits

async def list_products(update: Update, context: ContextTypes.DEFAULT_TYPE): query = update.callback_query await query.answer() products = load_products()

for p in products:
    promo = "🔥 Promo" if p.get('promo') else ""
    msg = f"📦 <b>{p['title']}</b>\n💰 Prix : {p['price']} FCFA\n🏷️ Catégorie : {p['category']}\n{promo}"
    keyboard = [[InlineKeyboardButton("Commander", callback_data=f"order|{p['title']}")]]
    await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

Commander un produit

async def order(update: Update, context: ContextTypes.DEFAULT_TYPE): query = update.callback_query _, title = query.data.split('|') context.user_data['order'] = title await query.answer() await query.message.reply_text( f"📝 Entrez maintenant l'ID de transaction + le mode de paiement (par ex : 123456 Orange Money) pour le produit : {title}" )

Réception ID de paiement

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE): if 'order' in context.user_data: detail = context.user_data.pop('order') user_input = update.message.text msg = f"✅ Reçu enregistré :\nProduit : {detail}\n🧾 Détails : {user_input}\nMerci d'envoyer ceci à @deku225." keyboard = [[InlineKeyboardButton("⬅️ Retour", callback_data='list')]] await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

Commande /avis

async def avis(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("⭐ Laissez votre avis en répondant à ce message ou contactez @deku225 directement.")

Gestion admin

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE): if update.effective_user.username != ADMIN_USERNAME.strip('@'): await update.message.reply_text("⛔ Accès refusé.") return

text = update.message.text.split(' ', 1)
if len(text) < 2:
    await update.message.reply_text("⚙️ Format invalide. Utilisez :\n/add title|price|category\n/del title\n/promo title")
    return

cmd, args = text[0], text[1]
products = load_products()

if cmd == '/add':
    title, price, category = args.split('|')
    products.append({"title": title, "price": int(price), "category": category})
    save_products(products)
    await update.message.reply_text(f"✅ Produit ajouté : {title}")
elif cmd == '/del':
    products = [p for p in products if p['title'] != args]
    save_products(products)
    await update.message.reply_text(f"🗑️ Produit supprimé : {args}")
elif cmd == '/promo':
    for p in products:
        if p['title'] == args:
            p['promo'] = True
    save_products(products)
    await update.message.reply_text(f"🔥 Promo activée sur : {args}")
else:
    await update.message.reply_text("Commande inconnue")

Dispatcher

app = ApplicationBuilder().token("VOTRE_TOKEN_BOT").build()

app.add_handler(CommandHandler("start", start)) app.add_handler(CallbackQueryHandler(list_products, pattern='^list$')) app.add_handler(CallbackQueryHandler(order, pattern='^order|')) app.add_handler(CommandHandler("avis", avis)) app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)) app.add_handler(MessageHandler(filters.TEXT & filters.User(username=ADMIN_USERNAME), admin))

if name == 'main': print("Bot lancé...") app.run_polling()

