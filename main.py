#!/usr/bin/env python3
"""
VAULTY CARD ANALYZER - BOT TELEGRAM
Version Française avec Promotion
© 2025 Vaulty Protocol 🇨🇭
"""

import os
import base64
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import anthropic

# Configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-20250514"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Prompt d'analyse en FRANÇAIS - Focus sur identification précise
ANALYSIS_PROMPT = """Tu es un expert certifié en cartes à collectionner avec 20+ ans d'expérience.

⚠️ RÈGLES ABSOLUES:

1. **IDENTIFICATION - SOIS PRÉCIS À 100%**:
   - Lis CHAQUE texte visible sur la carte (nom, set, numéro, année, rareté)
   - Identifie le JEU: Pokémon, One Piece TCG, Yu-Gi-Oh, Magic, Dragon Ball, Sports (NBA, NFL, etc.)
   - Identifie le SET EXACT avec son code (ex: EB01, SV04, etc.)
   - Identifie la RARETÉ/PARALLÈLE exact:
     * One Piece: Common, Uncommon, Rare, Super Rare, Secret Rare, Manga Rare, Treasure Rare, Special Art
     * Pokémon: Common, Uncommon, Rare, Holo Rare, V, VMAX, VSTAR, Alt Art, Special Art Rare, Hyper Rare
     * Sports: Base, Prizm, Silver Prizm, Gold, Numbered /99 /25 /10 /1
   - Si gradée, lis le LABEL COMPLET (compagnie, note, numéro certification)

2. **ÉTAT - SOIS CRITIQUE**:
   - Examine attentivement: centrage, coins, surface, bordures
   - Note les défauts visibles
   - Donne une note PSA équivalente réaliste

3. **PRIX - SOIS HONNÊTE**:
   - Indique "VÉRIFIEZ SUR EBAY SOLD" car tu n'as PAS accès aux prix en temps réel
   - Donne une FOURCHETTE INDICATIVE basée sur la rareté de la carte
   - Ne donne JAMAIS de prix précis comme si c'était la réalité

Réponds EN FRANÇAIS avec ce format:

🎴 **IDENTIFICATION COMPLÈTE**
• Jeu: [Pokémon / One Piece TCG / Yu-Gi-Oh / Magic / Sports / etc.]
• Carte: [Nom EXACT visible sur la carte]
• Set: [Nom complet + code, ex: "Memorial Collection EB01"]
• Numéro: [Code exact, ex: EB01-051]
• Rareté: [Rareté EXACTE - Common/Rare/Super Rare/Treasure Rare/etc.]
• Parallèle: [Si applicable: Manga Rare, Alt Art, Gold Border, etc.]
• Langue: [FR/EN/JP]
• Gradée: [Non / Oui → Compagnie + Note + N° certification]

📊 **ÉVALUATION DE L'ÉTAT**
• Note estimée: [X/10] (équivalent PSA)
• Centrage: [XX/XX] - [Excellent/Bon/Moyen/Décentré]
• Coins: [Description précise]
• Surface: [Description précise]
• Bordures: [Description précise]
• Défauts: [Liste ou "Aucun défaut majeur visible"]

💰 **ESTIMATION INDICATIVE**

⚠️ **IMPORTANT**: Ces prix sont des ESTIMATIONS. Vérifiez les ventes réelles sur eBay Sold !

📦 **RAW** (non gradée): [Fourchette large basée sur la rareté]
🏆 **PSA 10**: [Estimation si cette carte est recherchée gradée]
🏅 **PSA 9**: [Estimation]

🔎 **Pour le prix RÉEL**: Recherchez "[Nom carte] [Set] [Rareté] sold" sur eBay

📈 **POTENTIEL**: [Cette carte est-elle recherchée ? Populaire ? Rare ?]

💡 **RECOMMANDATION**: [CONSERVER / VENDRE / FAIRE GRADER]
[Explication basée sur la rareté et l'état]

💎 **CONSEIL VAULTY**: [Conseil sur la protection/certification]

---
🔐 *Analyse Vaulty Protocol • vaultyprotocol.tech*
"""

async def analyze_card(image_bytes: bytes) -> str:
    """Analyse une carte via Claude API"""
    if not ANTHROPIC_API_KEY:
        return """❌ **Erreur de configuration**

Le service d'analyse n'est pas disponible pour le moment.

En attendant, découvrez nos services sur:
🌐 **vaultyprotocol.tech**

Ou contactez-nous pour une expertise manuelle !"""

    try:
        image_base64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        message = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_base64}},
                    {"type": "text", "text": ANALYSIS_PROMPT}
                ],
            }],
        )
        return message.content[0].text
    except Exception as e:
        logger.error(f"Erreur API: {e}")
        return f"""❌ **Erreur lors de l'analyse**

Détails: {str(e)}

Réessayez ou visitez notre site pour une expertise manuelle:
🌐 **vaultyprotocol.tech**"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Commande /start"""
    welcome = """
🎴 **VAULTY CARD ANALYZER**
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Bienvenue sur le bot officiel de **Vaulty Protocol** ! 🇨🇭

Je suis votre assistant IA pour l'analyse de cartes à collectionner (Pokémon, Football, Basketball, etc.)

📸 **Envoyez-moi une photo** et j'analyserai:
✅ Identification complète de la carte
✅ Estimation de l'état (1-10)
✅ Prix de marché (RAW & gradé)
✅ Tendance et recommandation

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔐 **POURQUOI VAULTY PROTOCOL ?**

Nous sommes le premier service suisse d'authentification de cartes par blockchain:

• 🛡️ **Protection anti-contrefaçon** - Hologramme VOID + puce NFC
• ⛓️ **Certificat blockchain** - NFT sur Polygon infalsifiable
• 🔍 **Empreinte digitale unique** - Chaque carte a son identité
• 🇨🇭 **Qualité Suisse** - Inspection minutieuse

━━━━━━━━━━━━━━━━━━━━━━━━━━━

📷 **Envoyez une photo pour commencer !**

🎯 Commandes: /help • /services • /prix • /contact
"""
    keyboard = [
        [
            InlineKeyboardButton("🌐 Découvrir Vaulty", url="https://vaultyprotocol.tech"),
            InlineKeyboardButton("🛒 Marketplace", url="https://vaultyprotocol.tech/marketplace/"),
        ],
        [
            InlineKeyboardButton("🔐 Nos Services", url="https://vaultyprotocol.tech/pass-services/"),
            InlineKeyboardButton("✅ Vérifier une Carte", url="https://vaultyprotocol.tech/vaultyprotocol-tech-verify/"),
        ],
        [
            InlineKeyboardButton("📱 Instagram", url="https://instagram.com/vaulty_protocol"),
            InlineKeyboardButton("🐦 Twitter/X", url="https://x.com/vaulty_protocol"),
        ],
    ]
    await update.message.reply_text(welcome, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Commande /help"""
    help_text = """
📖 **AIDE - VAULTY CARD ANALYZER**
━━━━━━━━━━━━━━━━━━━━━━━━━━━

**📸 ANALYSER UNE CARTE**
1. Prenez une photo claire de votre carte
2. Envoyez-la dans ce chat
3. Attendez l'analyse IA (5-15 sec)

**💡 CONSEILS PHOTO**
• Bonne lumière, pas de reflets
• Carte entière visible
• Si gradée, montrez le label PSA/BGS

**📊 CE QUE VOUS OBTENEZ**
• Identification (joueur, set, année)
• Estimation de condition (1-10)
• Prix RAW et gradé (€ et CHF)
• Tendance du marché
• Recommandation personnalisée

━━━━━━━━━━━━━━━━━━━━━━━━━━━

**🎯 COMMANDES**
/start - Message de bienvenue
/help - Cette aide
/services - Nos services de certification
/prix - Tarifs Vaulty Protocol
/verifier - Vérifier une carte certifiée
/contact - Nous contacter

━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ *Les estimations sont basées sur les données de marché. Consultez eBay Sold pour les prix actuels.*

🌐 **vaultyprotocol.tech**
"""
    keyboard = [[InlineKeyboardButton("🌐 Visiter notre site", url="https://vaultyprotocol.tech")]]
    await update.message.reply_text(help_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def services_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Commande /services"""
    services_text = """
🔐 **NOS SERVICES DE CERTIFICATION**
━━━━━━━━━━━━━━━━━━━━━━━━━━━

**🥉 FORFAIT BRONZE** - dès 15 CHF
• Inspection visuelle complète
• Certificat numérique
• QR Code de vérification
→ Idéal pour les cartes < 50€

**🥈 FORFAIT ARGENT** - dès 35 CHF
• Tout Bronze +
• Hologramme VOID anti-ouverture
• Puce NFC cryptographique
• NFT sur blockchain Polygon
→ Recommandé pour cartes 50-200€

**🥇 FORFAIT OR** - dès 75 CHF
• Tout Argent +
• Boîtier de protection premium
• Mesures physiques précises
• Empreinte digitale complète
→ Pour vos cartes de valeur 200€+

━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ **AVANTAGES VAULTY**
• Vendez 25-50% plus cher
• Confiance acheteur immédiate
• Protection anti-contrefaçon
• Traçabilité blockchain
• Qualité Suisse 🇨🇭

━━━━━━━━━━━━━━━━━━━━━━━━━━━
📷 *Envoyez une photo pour une estimation gratuite !*
"""
    keyboard = [
        [InlineKeyboardButton("🔐 Commander une Certification", url="https://vaultyprotocol.tech/pass-services/")],
        [InlineKeyboardButton("🛒 Voir le Marketplace", url="https://vaultyprotocol.tech/marketplace/")],
        [InlineKeyboardButton("📞 Nous Contacter", url="https://vaultyprotocol.tech/contact/")],
    ]
    await update.message.reply_text(services_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def prix_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Commande /prix"""
    prix_text = """
💰 **TARIFS VAULTY PROTOCOL**
━━━━━━━━━━━━━━━━━━━━━━━━━━━

**📦 CARTES GRADÉES (PSA, BGS, CGC)**

🥉 Bronze: **15-19 CHF**
🥈 Argent: **35-45 CHF**
🥇 Or: **75-95 CHF**

**🃏 CARTES RAW (non gradées)**

🥉 Bronze: **19-25 CHF**
🥈 Argent: **45-55 CHF**
🥇 Or: **95-115 CHF**

━━━━━━━━━━━━━━━━━━━━━━━━━━━

**💎 SERVICES ADDITIONNELS**

• Rapport de Collection: 19-49 CHF
• Évaluation Assurance: 29 CHF
• Alerte Prix Premium: 5-9 CHF/mois

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎁 **OFFRE SPÉCIALE**
-10% sur votre première certification !
Code: **TELEGRAM10**

━━━━━━━━━━━━━━━━━━━━━━━━━━━
📷 *Envoyez une photo pour savoir quel forfait vous convient !*
"""
    keyboard = [
        [InlineKeyboardButton("🔐 Commander Maintenant", url="https://vaultyprotocol.tech/pass-services/")],
        [InlineKeyboardButton("💬 Demander un Devis", url="https://vaultyprotocol.tech/contact/")],
    ]
    await update.message.reply_text(prix_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def verifier_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Commande /verifier"""
    verifier_text = """
✅ **VÉRIFIER UNE CARTE VAULTY**
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Vous avez acheté une carte certifiée Vaulty ?
Vérifiez son authenticité en 2 secondes !

**🔍 COMMENT VÉRIFIER ?**

1️⃣ **Par QR Code**
Scannez le QR sur le certificat

2️⃣ **Par ID Vaulty**
Entrez le code VLT-XXX-XXX-XXXXXX sur notre site

3️⃣ **Par NFC** (Forfait Argent/Or)
Approchez votre téléphone de la puce

━━━━━━━━━━━━━━━━━━━━━━━━━━━

**🛡️ CE QUE VOUS VOYEZ**
• Photo originale de la carte
• Empreinte digitale unique
• Historique complet
• Certificat blockchain
• Lien OpenSea du NFT

━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ *Si la vérification échoue, contactez-nous immédiatement !*
"""
    keyboard = [
        [InlineKeyboardButton("✅ Vérifier une Carte", url="https://vaultyprotocol.tech/vaultyprotocol-tech-verify/")],
        [InlineKeyboardButton("⚠️ Signaler un Problème", url="https://vaultyprotocol.tech/contact/")],
    ]
    await update.message.reply_text(verifier_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Commande /contact"""
    contact_text = """
📞 **CONTACTEZ VAULTY PROTOCOL**
━━━━━━━━━━━━━━━━━━━━━━━━━━━

**🌐 Site Web**
vaultyprotocol.tech

**📧 Email**
contact@vaultyprotocol.tech

**📱 Réseaux Sociaux**
• Twitter/X: @vaulty_protocol
• Instagram: @vaulty_protocol
• TikTok: @vaulty_protocol

**💬 Discord**
Rejoignez notre communauté !

━━━━━━━━━━━━━━━━━━━━━━━━━━━

**📍 Localisation**
Suisse 🇨🇭

**⏰ Horaires**
Lun-Ven: 9h-18h (CET)
Réponse sous 24-48h

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔐 *Vaulty Protocol - Swiss Blockchain Authentication*
"""
    keyboard = [
        [
            InlineKeyboardButton("🌐 Site Web", url="https://vaultyprotocol.tech"),
            InlineKeyboardButton("📧 Email", url="mailto:contact@vaultyprotocol.tech"),
        ],
        [
            InlineKeyboardButton("🐦 Twitter", url="https://x.com/vaulty_protocol"),
            InlineKeyboardButton("📱 Instagram", url="https://instagram.com/vaulty_protocol"),
        ],
    ]
    await update.message.reply_text(contact_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Traite les photos"""
    user = update.message.from_user
    logger.info(f"Photo reçue de {user.username or user.id}")

    waiting = await update.message.reply_text(
        "🔄 **Analyse en cours...**\n\n"
        "⏳ Identification de la carte\n"
        "⏳ Évaluation de l'état\n"
        "⏳ Recherche des prix de marché\n\n"
        "_Propulsé par Vaulty Protocol 🇨🇭_",
        parse_mode="Markdown"
    )

    try:
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        image_bytes = await photo_file.download_as_bytearray()

        result = await analyze_card(bytes(image_bytes))
        await waiting.delete()

        # Envoyer résultat
        if len(result) > 4000:
            for i in range(0, len(result), 4000):
                await update.message.reply_text(result[i:i+4000], parse_mode="Markdown")
        else:
            await update.message.reply_text(result, parse_mode="Markdown")

        # Message avec liens pour vérifier les prix réels
        price_check_message = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔎 **VÉRIFIEZ LE PRIX RÉEL**

Cliquez ci-dessous pour voir les **dernières ventes** de cartes similaires:

━━━━━━━━━━━━━━━━━━━━━━━━━━━

💎 **PROTÉGEZ CETTE CARTE !**

Certification Vaulty Protocol:
✅ Vendez **25-50% plus cher**
✅ Certificat **blockchain**
✅ Protection **NFC + Hologramme**

🎁 **-10% avec TELEGRAM10**

━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        keyboard = [
            [
                InlineKeyboardButton("🔍 eBay Sold", url="https://www.ebay.fr/sch/i.html?_nkw=&LH_Complete=1&LH_Sold=1"),
                InlineKeyboardButton("🛒 CardMarket", url="https://www.cardmarket.com/"),
            ],
            [InlineKeyboardButton("🔐 Certifier cette carte", url="https://vaultyprotocol.tech/pass-services/")],
            [
                InlineKeyboardButton("💰 Nos tarifs", url="https://vaultyprotocol.tech/pass-services/"),
                InlineKeyboardButton("🛒 Marketplace", url="https://vaultyprotocol.tech/marketplace/"),
            ],
        ]
        await update.message.reply_text(
            price_check_message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"Erreur: {e}")
        await waiting.edit_text(
            f"❌ **Erreur lors de l'analyse**\n\n"
            f"Détails: {str(e)}\n\n"
            f"Réessayez ou visitez:\n"
            f"🌐 **vaultyprotocol.tech**",
            parse_mode="Markdown"
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère les messages texte"""
    text = update.message.text.lower()

    # Réponses intelligentes en français
    if any(word in text for word in ["bonjour", "salut", "hello", "hi", "coucou", "hey"]):
        response = """
👋 **Bonjour !** Bienvenue sur Vaulty Card Analyzer !

📷 Envoyez-moi une photo de votre carte pour:
• Identification complète
• Estimation de prix
• Recommandation personnalisée

🌐 Découvrez nos services: vaultyprotocol.tech
"""
    elif any(word in text for word in ["merci", "thanks", "super", "génial", "cool", "parfait"]):
        response = """
🙏 **Avec plaisir !**

N'hésitez pas à:
• 📷 Analyser d'autres cartes
• 🔐 Découvrir nos certifications
• 🛒 Visiter notre marketplace

🌐 **vaultyprotocol.tech**
"""
    elif any(word in text for word in ["prix", "tarif", "coût", "combien", "coute"]):
        response = """
💰 **Nos tarifs commencent à 15 CHF !**

🥉 Bronze: dès 15 CHF
🥈 Argent: dès 35 CHF
🥇 Or: dès 75 CHF

🎁 **-10% avec TELEGRAM10**

Tapez /prix pour plus de détails !
"""
    elif any(word in text for word in ["faux", "fake", "contrefaçon", "arnaque", "scam"]):
        response = """
🛡️ **Protégez-vous des contrefaçons !**

~30% des cartes gradées en ligne sont fausses !

Vaulty Protocol vous protège avec:
• Empreinte digitale unique
• Puce NFC cryptographique
• Certificat blockchain
• Hologramme VOID

🌐 **vaultyprotocol.tech/pass-services/**
"""
    elif any(word in text for word in ["aide", "help", "comment", "quoi"]):
        response = """
📖 **Besoin d'aide ?**

📷 **Pour analyser:** Envoyez une photo
🎯 **Commandes:** /help, /services, /prix

🌐 Plus d'infos: vaultyprotocol.tech
"""
    else:
        response = """
🤔 Je ne comprends que les photos de cartes !

📷 **Envoyez une image** pour l'analyser.

🎯 **Commandes utiles:**
• /help - Aide
• /services - Nos services
• /prix - Tarifs

🌐 **vaultyprotocol.tech**
"""

    keyboard = [[InlineKeyboardButton("🌐 Visiter le site", url="https://vaultyprotocol.tech")]]
    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

def main() -> None:
    """Lance le bot"""
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN non configuré!")
        return
    if not ANTHROPIC_API_KEY:
        print("⚠️ ANTHROPIC_API_KEY non configuré!")

    print("🎴 Vaulty Card Analyzer - Bot Telegram")
    print("🇨🇭 Version Française avec Promotion")
    print("✅ Démarrage...")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Commandes
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("aide", help_command))
    app.add_handler(CommandHandler("services", services_command))
    app.add_handler(CommandHandler("prix", prix_command))
    app.add_handler(CommandHandler("tarifs", prix_command))
    app.add_handler(CommandHandler("verifier", verifier_command))
    app.add_handler(CommandHandler("verify", verifier_command))
    app.add_handler(CommandHandler("contact", contact_command))

    # Handlers
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("✅ Bot prêt ! En attente de messages...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
