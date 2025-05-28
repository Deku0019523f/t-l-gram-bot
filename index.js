const { Telegraf, Markup } = require('telegraf');
require('dotenv').config();

const bot = new Telegraf(process.env.BOT_TOKEN);

bot.start((ctx) => {
    const username = ctx.from.username || ctx.from.first_name || "utilisateur";
    ctx.replyWithMarkdown(`🎉 Bienvenue *${username}* sur Deku Shop !

Voici nos options :`, Markup.keyboard([
        ['🛍️ Produits', '🛒 Commander'],
        ['💬 Avis', '📞 Contacter un agent']
    ]).resize());
});

bot.hears('🛍️ Produits', (ctx) => {
    ctx.replyWithMarkdown(`📦 *Produits disponibles :*
1. Forfait VPN - 1000 FCFA
2. Combo 3 VPN - 2500 FCFA

Utilisez le bouton "Commander" pour acheter.`);
});

bot.hears('🛒 Commander', (ctx) => {
    ctx.replyWithMarkdown(`💳 *Modes de Paiement :*

📱 *Orange* : +225 0718623773
📱 *MTN* : +225 0575719113
📱 *Wave* : +225 0596430369

Après paiement, envoyez votre *ID de transaction* ici pour recevoir votre fichier.

Contact : [@deku225](https://t.me/deku225)`, { disable_web_page_preview: true });
});

bot.hears('💬 Avis', (ctx) => {
    ctx.reply('⭐ N’hésitez pas à nous laisser un avis sur @deku225 !');
});

bot.hears('📞 Contacter un agent', (ctx) => {
    ctx.reply('📞 Contactez notre support : @deku225');
});

bot.launch();