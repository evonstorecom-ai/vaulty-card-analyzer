#!/usr/bin/env python3
"""
VAULTY CARD ANALYZER - BOT TELEGRAM
Version Française avec Promotion + Base de Prix Vérifiés
© 2025 Vaulty Protocol 🇨🇭
"""

import os
import re
import base64
import logging
import urllib.parse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import anthropic

# Import du système de prix
try:
    from database import db_manager
    import price_estimator
    PRICING_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Système de prix non disponible: {e}")
    PRICING_AVAILABLE = False

# Import du système de recherche externe (Google Lens, APIs externes)
try:
    from external_search import ExternalCardSearch, identify_card_external
    EXTERNAL_SEARCH_AVAILABLE = True
    external_searcher = ExternalCardSearch()
except ImportError as e:
    print(f"⚠️ Recherche externe non disponible: {e}")
    EXTERNAL_SEARCH_AVAILABLE = False
    external_searcher = None

# Configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-20250514"

# Admin IDs (séparés par des virgules dans la variable d'environnement)
ADMIN_IDS = set()
admin_env = os.environ.get("ADMIN_USER_IDS", "")
if admin_env:
    for aid in admin_env.split(","):
        try:
            ADMIN_IDS.add(int(aid.strip()))
        except ValueError:
            pass

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    """Vérifie si l'utilisateur est admin"""
    return user_id in ADMIN_IDS

# Prompt d'analyse en FRANÇAIS - IDENTIFICATION ET ÉTAT UNIQUEMENT (pas de prix)
ANALYSIS_PROMPT = """Tu es un expert certifié en cartes à collectionner avec 20+ ans d'expérience.

⚠️ RÈGLES ABSOLUES:

1. **IDENTIFICATION - SOIS PRÉCIS À 100%**:
   - Lis CHAQUE texte visible sur la carte (nom, set, numéro, année, rareté)
   - Identifie le JEU: Pokémon, One Piece TCG, Yu-Gi-Oh, Magic, Dragon Ball, Sports (NBA, NFL, etc.)
   - Identifie le SET EXACT avec son code (ex: EB01, SV04, etc.)
   - Identifie la RARETÉ/PARALLÈLE exact
   - Si gradée, lis le LABEL COMPLET (compagnie, note, numéro certification)

2. **ÉTAT - SOIS CRITIQUE**:
   - Examine attentivement: centrage, coins, surface, bordures
   - Note les défauts visibles
   - Donne une note PSA équivalente réaliste

3. **PAS DE PRIX** - NE DONNE AUCUNE ESTIMATION DE PRIX (le système le fait automatiquement)

Réponds EN FRANÇAIS avec ce format COMPACT:

🎴 **[NOM DU JOUEUR/PERSONNAGE]**
━━━━━━━━━━━━━━━━━━━━

📦 Set: [Nom complet + code]
🔢 Numéro: [Code exact]
✨ Rareté: [Rareté + Parallèle si applicable]
🌍 Langue: [FR/EN/JP]
🏷️ Gradée: [Non / Oui → Compagnie + Note]

📊 **ÉTAT ESTIMÉ: [X/10]**
• Centrage: [Description courte]
• Surface: [Description courte]
• Coins/Bordures: [Description courte]
• Défauts: [Liste courte ou "Aucun"]

📈 **POTENTIEL**: [Carte recherchée ? Populaire ? Rare ? Tendance du marché - 1-2 phrases]

💡 **CONSEIL**: [CONSERVER / VENDRE / FAIRE GRADER - avec justification courte]

💎 **CONSEIL VAULTY**: [Conseil sur la protection ou certification - 1 phrase]
🔗 vaultyprotocol.tech
"""


def generate_search_urls(card_name: str, set_name: str, game: str) -> dict:
    """Génère des URLs de recherche pour vérifier les prix réels"""
    # Nettoyer le nom de la carte pour la recherche
    search_query = f"{card_name} {set_name}".strip()
    encoded_query = urllib.parse.quote(search_query)

    urls = {
        "ebay_sold": f"https://www.ebay.fr/sch/i.html?_nkw={encoded_query}&LH_Complete=1&LH_Sold=1",
        "ebay_active": f"https://www.ebay.fr/sch/i.html?_nkw={encoded_query}",
    }

    # URLs spécifiques selon le jeu
    game_lower = game.lower() if game else ""

    if "pokemon" in game_lower or "pokémon" in game_lower:
        urls["cardmarket"] = f"https://www.cardmarket.com/fr/Pokemon/Products/Search?searchString={encoded_query}"
        urls["tcgplayer"] = f"https://www.tcgplayer.com/search/pokemon/product?q={encoded_query}"
    elif "one piece" in game_lower:
        urls["cardmarket"] = f"https://www.cardmarket.com/fr/OnePiece/Products/Search?searchString={encoded_query}"
        urls["tcgplayer"] = f"https://www.tcgplayer.com/search/one-piece-card-game/product?q={encoded_query}"
    elif "yu-gi-oh" in game_lower or "yugioh" in game_lower:
        urls["cardmarket"] = f"https://www.cardmarket.com/fr/YuGiOh/Products/Search?searchString={encoded_query}"
        urls["tcgplayer"] = f"https://www.tcgplayer.com/search/yugioh/product?q={encoded_query}"
    elif "magic" in game_lower:
        urls["cardmarket"] = f"https://www.cardmarket.com/fr/Magic/Products/Search?searchString={encoded_query}"
        urls["tcgplayer"] = f"https://www.tcgplayer.com/search/magic/product?q={encoded_query}"
    else:
        urls["cardmarket"] = f"https://www.cardmarket.com/fr/search?searchString={encoded_query}"
        urls["tcgplayer"] = f"https://www.tcgplayer.com/search/all/product?q={encoded_query}"

    return urls


def extract_card_info(analysis_text: str) -> dict:
    """Extrait les informations de la carte depuis l'analyse Claude"""
    info = {
        "game": "",
        "card_name": "",
        "set_name": "",
        "number": "",
        "rarity": ""
    }

    lines = analysis_text.split('\n')
    for line in lines:
        line_lower = line.lower()

        # Nouveau format avec emojis
        if "📦 set:" in line_lower or "📦 set :" in line_lower:
            info["set_name"] = line.split(":", 1)[-1].strip()
        elif "🔢 numéro:" in line_lower or "🔢 numéro :" in line_lower:
            info["number"] = line.split(":", 1)[-1].strip()
        elif "✨ rareté:" in line_lower or "✨ rareté :" in line_lower:
            info["rarity"] = line.split(":", 1)[-1].strip()
        elif "🌍 langue:" in line_lower:
            pass  # On ignore la langue
        elif "🏷️ gradée:" in line_lower:
            pass  # On ignore le grade
        # Ancien format (compatibilité)
        elif "• jeu:" in line_lower or "• jeu :" in line_lower:
            info["game"] = line.split(":", 1)[-1].strip()
        elif "• carte:" in line_lower or "• carte :" in line_lower:
            info["card_name"] = line.split(":", 1)[-1].strip()
        elif "• set:" in line_lower or "• set :" in line_lower:
            info["set_name"] = line.split(":", 1)[-1].strip()
        elif "• numéro:" in line_lower or "• numéro :" in line_lower:
            info["number"] = line.split(":", 1)[-1].strip()
        elif "• rareté:" in line_lower or "• rareté :" in line_lower:
            info["rarity"] = line.split(":", 1)[-1].strip()
        # Extraire le nom du joueur/personnage depuis le header
        elif line.startswith("🎴 **") and "**" in line[5:]:
            # Format: 🎴 **NOM DU JOUEUR**
            name = line.replace("🎴 **", "").replace("**", "").strip()
            if name:
                info["card_name"] = name

    # Détecter le jeu depuis le set si pas trouvé
    if not info["game"] and info["set_name"]:
        set_lower = info["set_name"].lower()
        if "pokemon" in set_lower or "pokémon" in set_lower:
            info["game"] = "Pokemon"
        elif "one piece" in set_lower or "op01" in set_lower or "op02" in set_lower:
            info["game"] = "One Piece TCG"
        elif "prizm" in set_lower or "topps" in set_lower or "fleer" in set_lower or "panini" in set_lower:
            info["game"] = "Sports"
        elif "yu-gi-oh" in set_lower or "lob" in set_lower:
            info["game"] = "Yu-Gi-Oh"
        elif "magic" in set_lower or "mtg" in set_lower:
            info["game"] = "Magic"

    return info


def lookup_verified_prices(card_info: dict) -> str | None:
    """
    Recherche les prix dans la base de données et l'algorithme.
    Utilise le module price_estimator pour des résultats cohérents.
    Retourne un message formaté, ou None si module non disponible.
    """
    if not PRICING_AVAILABLE:
        return None

    game = card_info.get("game", "")
    card_name = card_info.get("card_name", "")
    set_name = card_info.get("set_name", "")
    number = card_info.get("number", "")
    rarity = card_info.get("rarity", "")

    # Utiliser le module price_estimator
    return price_estimator.format_price_for_analysis(
        game=game,
        card_name=card_name,
        set_name=set_name,
        number=number,
        rarity=rarity
    )


async def analyze_card_with_external(image_bytes: bytes) -> tuple:
    """
    Analyse hybride: Claude Vision + Recherche externe (Google Lens, APIs).
    Retourne (result_text, external_data)
    """
    external_data = None

    # 1. RECHERCHE EXTERNE EN PREMIER (Google Lens + APIs)
    if EXTERNAL_SEARCH_AVAILABLE and external_searcher:
        try:
            logger.info("🔍 Recherche externe en cours (Google Lens + APIs)...")
            external_data = await identify_card_external(image_bytes)

            if external_data.get("success"):
                logger.info(f"✅ Recherche externe réussie: {external_data.get('best_match', {}).get('name', 'N/A')}")
            else:
                logger.info("⚠️ Recherche externe: pas de résultat concluant")

        except Exception as e:
            logger.error(f"Erreur recherche externe: {e}")
            external_data = {"success": False, "error": str(e)}

    # 2. ANALYSE CLAUDE VISION
    claude_result = await analyze_card_claude(image_bytes, external_data)

    return claude_result, external_data


async def analyze_card_claude(image_bytes: bytes, external_hints: dict = None) -> str:
    """Analyse via Claude API avec hints externes optionnels"""
    if not ANTHROPIC_API_KEY:
        return """❌ **Erreur de configuration**

Le service d'analyse n'est pas disponible pour le moment.

En attendant, découvrez nos services sur:
🌐 **vaultyprotocol.tech**

Ou contactez-nous pour une expertise manuelle !"""

    try:
        image_base64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        # Enrichir le prompt avec les infos externes si disponibles
        enhanced_prompt = ANALYSIS_PROMPT

        if external_hints and external_hints.get("success"):
            best_match = external_hints.get("best_match", {})
            all_matches = external_hints.get("all_matches", [])

            if best_match.get("name") or all_matches:
                hints_text = "\n\n🔍 **INDICES DE RECHERCHE EXTERNE** (à vérifier avec l'image):\n"

                if best_match.get("name"):
                    hints_text += f"- Carte possiblement identifiée: {best_match.get('name')}\n"
                    if best_match.get("game"):
                        hints_text += f"- Jeu détecté: {best_match.get('game')}\n"
                    if best_match.get("set"):
                        hints_text += f"- Set possible: {best_match.get('set')}\n"

                for match in all_matches[:2]:
                    if match.get("name"):
                        hints_text += f"- Match API ({match.get('source')}): {match.get('name')} - {match.get('set', 'N/A')}\n"

                # Ajouter les prix externes trouvés
                prices = external_hints.get("prices", {})
                if prices:
                    hints_text += "\n📊 **Prix de référence externes**:\n"
                    if "scryfall" in prices:
                        p = prices["scryfall"]
                        hints_text += f"- Scryfall: ${p.get('usd', 0)} (normal), ${p.get('usd_foil', 0)} (foil)\n"
                    if "pokemon_tcg" in prices:
                        p = prices["pokemon_tcg"]
                        hints_text += f"- Pokemon TCG: ${p.get('market', p.get('mid', 0))} (market)\n"
                    if "ebay_sold" in prices:
                        p = prices["ebay_sold"]
                        if p.get("avg"):
                            hints_text += f"- eBay Sold: ${p.get('avg'):.2f} avg (min: ${p.get('min', 0):.2f}, max: ${p.get('max', 0):.2f})\n"

                enhanced_prompt += hints_text
                enhanced_prompt += "\n⚠️ UTILISE ces indices pour confirmer ton identification, mais base-toi TOUJOURS sur ce que tu vois dans l'image."

        message = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_base64}},
                    {"type": "text", "text": enhanced_prompt}
                ],
            }],
        )
        return message.content[0].text
    except Exception as e:
        logger.error(f"Erreur API Claude: {e}")
        return f"""❌ **Erreur lors de l'analyse**

Détails: {str(e)}

Réessayez ou visitez notre site pour une expertise manuelle:
🌐 **vaultyprotocol.tech**"""


async def analyze_card(image_bytes: bytes) -> str:
    """Fonction de compatibilité - utilise le système hybride"""
    result, _ = await analyze_card_with_external(image_bytes)
    return result

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
    """Traite les photos avec système hybride (Claude + recherche externe)"""
    user = update.message.from_user
    logger.info(f"Photo reçue de {user.username or user.id}")

    waiting = await update.message.reply_text(
        "🔄 **Analyse en cours...**\n\n"
        "⏳ Recherche dans les bases de données...\n"
        "⏳ Identification via Google Lens...\n"
        "⏳ Analyse IA avancée...\n"
        "⏳ Vérification des prix de marché...\n\n"
        "_Propulsé par Vaulty Protocol 🇨🇭_",
        parse_mode="Markdown"
    )

    try:
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        image_bytes = await photo_file.download_as_bytearray()

        # Utiliser le système hybride
        result, external_data = await analyze_card_with_external(bytes(image_bytes))
        await waiting.delete()

        # Extraire les infos de la carte
        card_info = extract_card_info(result)

        # Rechercher les prix vérifiés dans la base
        verified_prices_msg = lookup_verified_prices(card_info)

        # Construire le message final
        if verified_prices_msg:
            # Retirer la section prix de Claude (estimations) et remplacer par prix vérifiés
            # On garde l'identification et l'évaluation de l'état
            final_result = result
            # Ajouter les prix vérifiés à la fin
            final_result = final_result + "\n\n" + verified_prices_msg
        else:
            # Pas de prix vérifié, ajouter un avertissement
            final_result = result + "\n\n⚠️ _Prix non vérifiés - Consultez eBay Sold pour les prix réels_"

        # Envoyer résultat
        if len(final_result) > 4000:
            for i in range(0, len(final_result), 4000):
                await update.message.reply_text(final_result[i:i+4000], parse_mode="Markdown")
        else:
            await update.message.reply_text(final_result, parse_mode="Markdown")
        # Utiliser les URLs externes si disponibles, sinon générer
        if external_data and external_data.get("search_urls"):
            search_urls = external_data["search_urls"]
            # S'assurer que toutes les clés existent
            if "ebay_sold" not in search_urls:
                search_urls["ebay_sold"] = generate_search_urls(
                    card_info.get("card_name", ""),
                    card_info.get("set_name", ""),
                    card_info.get("game", "")
                )["ebay_sold"]
        else:
            search_urls = generate_search_urls(
                card_info.get("card_name", ""),
                card_info.get("set_name", ""),
                card_info.get("game", "")
            )

        # Construire un message avec les prix externes trouvés
        external_prices_msg = ""
        if external_data and external_data.get("prices"):
            prices = external_data["prices"]
            external_prices_msg = "\n\n📊 **PRIX VÉRIFIÉS EN LIGNE:**\n"

            if "scryfall" in prices and prices["scryfall"].get("usd"):
                p = prices["scryfall"]
                external_prices_msg += f"• Scryfall: **${p.get('usd', 0)}** (foil: ${p.get('usd_foil', 0)})\n"

            if "pokemon_tcg" in prices and prices["pokemon_tcg"].get("market"):
                p = prices["pokemon_tcg"]
                external_prices_msg += f"• Pokemon TCG Market: **${p.get('market', 0):.2f}**\n"

            if "ebay_sold" in prices and prices["ebay_sold"].get("avg"):
                p = prices["ebay_sold"]
                external_prices_msg += f"• eBay Sold: **${p.get('avg', 0):.2f}** (range: ${p.get('min', 0):.2f} - ${p.get('max', 0):.2f})\n"

            if external_prices_msg == "\n\n📊 **PRIX VÉRIFIÉS EN LIGNE:**\n":
                external_prices_msg = ""  # Aucun prix trouvé

        # Ajouter les prix externes au résultat final si disponibles
        if external_prices_msg:
            final_result = final_result + external_prices_msg

        # Message avec liens et nom de la carte
        card_display = card_info.get("card_name", "cette carte")
        links_message = f"""━━━━━━━━━━━━━━━━━━━━
🔎 **VÉRIFIER LES PRIX RÉELS**
Recherchez **{card_display}** sur eBay Sold

🎁 **-10%** sur votre certification avec **TELEGRAM10**
"""
        keyboard = [
            [
                InlineKeyboardButton(f"🔍 eBay Sold", url=search_urls["ebay_sold"]),
                InlineKeyboardButton("🛒 CardMarket", url=search_urls.get("cardmarket", "https://www.cardmarket.com/")),
            ],
            [
                InlineKeyboardButton("🔐 Certifier cette carte", url="https://vaultyprotocol.tech/pass-services/"),
            ],
            [
                InlineKeyboardButton("🌐 vaultyprotocol.tech", url="https://vaultyprotocol.tech/"),
            ],
        ]
        await update.message.reply_text(
            links_message,
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


# ==================== COMMANDES ADMIN ====================

async def addprice_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Commande admin: /addprice [card_id] [grade] [min] [max]"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Commande réservée aux administrateurs.")
        return

    if not PRICING_AVAILABLE:
        await update.message.reply_text("❌ Système de prix non disponible.")
        return

    args = context.args
    if len(args) < 4:
        await update.message.reply_text(
            "**Usage:** `/addprice [card_id] [grade] [min] [max]`\n\n"
            "**Exemple:**\n"
            "`/addprice pokemon_pikachu_base_58 PSA_10 150 300`\n\n"
            "**Grades supportés:** RAW, PSA_7, PSA_8, PSA_9, PSA_10, BGS_9, BGS_9.5, BGS_10",
            parse_mode="Markdown"
        )
        return

    card_id = args[0]
    grade = args[1].upper().replace("-", "_")
    try:
        min_price = int(args[2])
        max_price = int(args[3])
    except ValueError:
        await update.message.reply_text("❌ Les prix doivent être des nombres entiers.")
        return

    # Vérifier si la carte existe
    existing = db_manager.find_card_exact(card_id)
    if existing:
        # Mise à jour
        db_manager.update_price(card_id, grade, min_price, max_price)
        await update.message.reply_text(
            f"✅ **Prix mis à jour !**\n\n"
            f"📦 Carte: `{card_id}`\n"
            f"📊 Grade: {grade}\n"
            f"💰 Prix: ${min_price} - ${max_price}",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"❌ Carte `{card_id}` non trouvée.\n\n"
            f"Pour créer une nouvelle carte, utilisez:\n"
            f"`/newcard [card_id] [name] [game] [set] [number]`",
            parse_mode="Markdown"
        )


async def newcard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Commande admin: /newcard pour ajouter une nouvelle carte"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Commande réservée aux administrateurs.")
        return

    if not PRICING_AVAILABLE:
        await update.message.reply_text("❌ Système de prix non disponible.")
        return

    # Format: /newcard card_id | name | game | set | number
    text = " ".join(context.args) if context.args else ""
    if "|" not in text:
        await update.message.reply_text(
            "**Usage:** `/newcard card_id | name | game | set | number`\n\n"
            "**Exemple:**\n"
            "`/newcard pokemon_mew_base_151 | Mew | Pokemon | Base Set | 151`",
            parse_mode="Markdown"
        )
        return

    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 5:
        await update.message.reply_text("❌ Format incorrect. Utilisez | comme séparateur.")
        return

    card_id, name, game, set_name, number = parts[:5]

    db_manager.add_price(card_id, name, game, set_name, number, "RAW", 0, 0)
    await update.message.reply_text(
        f"✅ **Carte créée !**\n\n"
        f"🆔 ID: `{card_id}`\n"
        f"📦 Nom: {name}\n"
        f"🎮 Jeu: {game}\n"
        f"📁 Set: {set_name}\n\n"
        f"Ajoutez des prix avec:\n"
        f"`/addprice {card_id} PSA_10 min max`",
        parse_mode="Markdown"
    )


async def listprices_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Commande admin: /listprices - Liste toutes les cartes"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Commande réservée aux administrateurs.")
        return

    if not PRICING_AVAILABLE:
        await update.message.reply_text("❌ Système de prix non disponible.")
        return

    cards = db_manager.list_all_cards()

    if not cards:
        await update.message.reply_text("📭 Aucune carte dans la base de données.")
        return

    # Grouper par jeu
    by_game = {}
    for card in cards:
        game = card.get("game", "Autre")
        if game not in by_game:
            by_game[game] = []
        by_game[game].append(card)

    response = "📊 **BASE DE DONNÉES DE PRIX**\n\n"

    for game, game_cards in by_game.items():
        response += f"**{game}** ({len(game_cards)} cartes)\n"
        for card in game_cards[:5]:  # Limiter à 5 par jeu
            grades = ", ".join(card.get("grades", []))
            response += f"• `{card['id'][:25]}...`\n  Grades: {grades}\n"
        if len(game_cards) > 5:
            response += f"  _...et {len(game_cards) - 5} autres_\n"
        response += "\n"

    stats = db_manager.get_stats()
    response += f"━━━━━━━━━━━━━━━━━━━\n"
    response += f"**Total:** {stats['total_cards']} cartes, {stats['total_prices']} prix"

    await update.message.reply_text(response, parse_mode="Markdown")


async def oldprices_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Commande admin: /oldprices - Prix à mettre à jour"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Commande réservée aux administrateurs.")
        return

    if not PRICING_AVAILABLE:
        await update.message.reply_text("❌ Système de prix non disponible.")
        return

    old_cards = db_manager.get_old_prices(months=3)

    if not old_cards:
        await update.message.reply_text("✅ Tous les prix sont à jour (< 3 mois) !")
        return

    response = "⚠️ **PRIX À METTRE À JOUR** (> 3 mois)\n\n"

    for card in old_cards[:15]:  # Limiter à 15
        response += f"• `{card['id'][:30]}`\n"
        response += f"  Dernière MAJ: {card['last_verified']} ({card['months_old']} mois)\n"

    if len(old_cards) > 15:
        response += f"\n_...et {len(old_cards) - 15} autres cartes_"

    await update.message.reply_text(response, parse_mode="Markdown")


async def searchdb_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Commande admin: /searchdb [query] - Recherche dans la base"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Commande réservée aux administrateurs.")
        return

    if not PRICING_AVAILABLE:
        await update.message.reply_text("❌ Système de prix non disponible.")
        return

    if not context.args:
        await update.message.reply_text("**Usage:** `/searchdb [mot-clé]`", parse_mode="Markdown")
        return

    query = " ".join(context.args)
    results = db_manager.search_cards(query, limit=10)

    if not results:
        await update.message.reply_text(f"❌ Aucun résultat pour '{query}'")
        return

    response = f"🔍 **Résultats pour '{query}':**\n\n"
    for card_id, card_data in results:
        prices = card_data.get("prices", {})
        grades = ", ".join(prices.keys())
        response += f"• **{card_data.get('name', 'N/A')}**\n"
        response += f"  ID: `{card_id}`\n"
        response += f"  Grades: {grades}\n\n"

    await update.message.reply_text(response, parse_mode="Markdown")


async def dbstats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Commande: /dbstats - Statistiques de la base"""
    if not PRICING_AVAILABLE:
        await update.message.reply_text("❌ Système de prix non disponible.")
        return

    stats = db_manager.get_stats()

    games_text = "\n".join([f"• {game}: {count}" for game, count in stats.get("games", {}).items()])

    response = f"""📊 **STATISTIQUES BASE DE DONNÉES**
━━━━━━━━━━━━━━━━━━━━━

**Cartes vérifiées:** {stats['total_cards']}
**Entrées de prix:** {stats['total_prices']}

**Par catégorie:**
{games_text}

**Dernière MAJ:** {stats.get('last_updated', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━
_Base de prix Vaulty Protocol_
"""
    await update.message.reply_text(response, parse_mode="Markdown")


async def adminhelp_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Commande admin: /adminhelp - Affiche l'aide admin"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Commande réservée aux administrateurs.")
        return

    help_text = """
👑 **MENU ADMIN - VAULTY CARD ANALYZER**
━━━━━━━━━━━━━━━━━━━━━

**📊 STATISTIQUES**
`/dbstats` → Voir les stats de la base
`/listprices` → Lister toutes les cartes
`/oldprices` → Prix > 3 mois à mettre à jour

**🔍 RECHERCHE**
`/searchdb [mot]` → Rechercher une carte
Exemple: `/searchdb charizard`

**➕ AJOUTER UNE CARTE**
`/newcard id | nom | jeu | set | numéro`
Exemple:
`/newcard pokemon_mew_base_151 | Mew | Pokemon | Base Set | 151`

**💰 AJOUTER UN PRIX**
`/addprice [id] [grade] [min] [max]`
Grades: RAW, PSA_7, PSA_8, PSA_9, PSA_10
Exemples:
`/addprice pokemon_mew_base_151 RAW 50 100`
`/addprice pokemon_mew_base_151 PSA_10 500 800`

━━━━━━━━━━━━━━━━━━━━━

**💡 WORKFLOW TYPIQUE:**
1. `/searchdb pikachu` → Vérifier si existe
2. `/newcard ...` → Créer si n'existe pas
3. `/addprice ... RAW ...` → Ajouter prix RAW
4. `/addprice ... PSA_10 ...` → Ajouter prix PSA 10
5. `/dbstats` → Vérifier les stats

━━━━━━━━━━━━━━━━━━━━━
🔐 _Admin Vaulty Protocol_
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")


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

    # Commandes admin (prix vérifiés)
    app.add_handler(CommandHandler("adminhelp", adminhelp_command))
    app.add_handler(CommandHandler("addprice", addprice_command))
    app.add_handler(CommandHandler("newcard", newcard_command))
    app.add_handler(CommandHandler("listprices", listprices_command))
    app.add_handler(CommandHandler("oldprices", oldprices_command))
    app.add_handler(CommandHandler("searchdb", searchdb_command))
    app.add_handler(CommandHandler("dbstats", dbstats_command))

    # Handlers
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("✅ Bot prêt ! En attente de messages...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
