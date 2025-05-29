import os
import json
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, CallbackQueryHandler, ContextTypes
)

TOKEN = os.getenv("BOT_TOKEN")

# Charger les produits depuis products.json au démarrage
def load_products():
    try:
        with open("products.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erreur chargement products.json : {e}")
        return []

products = load_products()

payment_numbers = {
    "Wave": "+2250575719113",
    "Orange": "+2250718623773",
    "MTN": "+2250596430369"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bienvenue sur le bot boutique !\n"
        "Tapez /produits pour voir la liste des produits."
    )

async def produits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not products:
        await update.message.reply_text("Aucun produit disponible actuellement.")
        return

    messages = []
    for p in products:
        promo_label = "🔥 Promo - " if p.get("promo", False) else ""
        message = (
            f"*{promo_label}{p['nom']}*\n"
            f"ID: `{p['id']}`\n"
            f"Prix: {p['prix']} FCFA\n"
            f"{p.get('description', '')}"
        )
        messages.append(message)

    full_message = "\n\n".join(messages)
    await update.message.reply_markdown(full_message)

async def avis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Merci pour votre avis ! Envoyez-nous un message avec vos impressions."
    )

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username == "@deku225":  # change ici le username admin
        await update.message.reply_text("Bienvenue admin.")
    else:
        await update.message.reply_text("Accès refusé.")

async def commande(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 3:
        await update.message.reply_text("Usage : /commande <product_id> <moyen_paiement> <transaction_id>")
        return

    product_id, moyen_paiement, transaction_id = args
    product = next((p for p in products if p["id"] == product_id), None)

    if not product:
        await update.message.reply_text("Produit non trouvé.")
        return

    if moyen_paiement not in payment_numbers:
        await update.message.reply_text(f"Moyen de paiement invalide. Choisissez parmi: {', '.join(payment_numbers.keys())}")
        return

    from datetime import datetime
    date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    payment_number = payment_numbers[moyen_paiement]

    receipt = f"""🧾 *Reçu de Commande*
Date : {date}
Produit : {product['nom']}
Prix : {product['prix']} FCFA
Moyen de paiement : {moyen_paiement}
Numéro : {payment_number}
Transaction ID : {transaction_id}

Merci pour votre achat !"""

    await update.message.reply_markdown(receipt)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"Update {update} caused error {context.error}")

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("produits", produits))
    application.add_handler(CommandHandler("avis", avis))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CommandHandler("commande", commande))

    application.add_error_handler(error_handler)

    print("✅ Bot en ligne !")
    application.run_polling()

if __name__ == "__main__":
    main()
