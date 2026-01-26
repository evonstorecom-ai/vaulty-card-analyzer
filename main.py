#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      VAULTY CARD ANALYZER - TELEGRAM BOT                      ║
║                    Trading Card Recognition & Valuation                       ║
║                         Powered by Claude Vision                              ║
║                                                                              ║
║  v2.0 - Now with verified price database for 80%+ accuracy                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

Telegram bot for analyzing collectible trading cards using AI vision.
Send a photo of your card and get instant identification and valuation.
"""

import base64
import json
import logging
import os
import sys
from io import BytesIO

try:
    import anthropic
except ImportError:
    print("❌ Error: anthropic package not installed. Run: pip install anthropic")
    sys.exit(1)

try:
    from telegram import Update
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        ContextTypes,
        filters,
    )
except ImportError:
    print("❌ Error: python-telegram-bot not installed. Run: pip install python-telegram-bot")
    sys.exit(1)

# Import Vaulty Pricing System
try:
    from vaulty_pricing import PriceEstimator, DatabaseManager, PriceFormatter
    from vaulty_pricing.config import ADMIN_USER_IDS
    PRICING_AVAILABLE = True
except ImportError:
    PRICING_AVAILABLE = False
    ADMIN_USER_IDS = []

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize pricing system
if PRICING_AVAILABLE:
    price_estimator = PriceEstimator()
    db_manager = DatabaseManager()
    price_formatter = PriceFormatter()
else:
    price_estimator = None
    db_manager = None
    price_formatter = None

# Admin user IDs from environment (comma-separated)
ADMIN_IDS = set(ADMIN_USER_IDS)
env_admins = os.environ.get("ADMIN_USER_IDS", "")
if env_admins:
    for admin_id in env_admins.split(","):
        try:
            ADMIN_IDS.add(int(admin_id.strip()))
        except ValueError:
            pass


def is_admin(user_id: int) -> bool:
    """Check if user is an admin."""
    return user_id in ADMIN_IDS


def escape_md(text) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    if text is None:
        return "N/A"
    text = str(text)
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def get_welcome_message() -> str:
    """Return the welcome message."""
    return """
🔷 *VAULTY CARD ANALYZER* 🔮
━━━━━━━━━━━━━━━━━━━━━━━━━━

Welcome to the AI\\-powered trading card analyzer\\!

📸 *How to use:*
Simply send me a photo of your trading card and I'll analyze it for you\\.

💎 *I can identify:*
• Player/Character name
• Card set and year
• Card number and parallels
• Rookie cards, autos, memorabilia

📊 *Price estimates with confidence levels:*
• 🟢 High confidence \\- Verified prices
• 🟡 Medium confidence \\- Algorithm estimate
• 🟠 Low confidence \\- Rough estimate
• 🔴 Unavailable \\- Check eBay Sold

━━━━━━━━━━━━━━━━━━━━━━━━━━
_Powered by Vaulty Protocol × Claude Vision_
_v2\\.0 \\- Verified Price Database_
"""


def get_analyzing_message() -> str:
    """Return the analyzing status message."""
    return "🔮 *Analyzing your card with AI vision\\.\\.\\.*\n\n_This may take a few seconds\\._"


def format_analysis_result(analysis: dict, price_estimates: dict = None) -> str:
    """Format the analysis result for Telegram with MarkdownV2."""
    ident = analysis.get("identification", {})
    condition = analysis.get("condition_assessment", {})
    ai_values = analysis.get("market_values", {})
    confidence = analysis.get("confidence", {})
    desc = analysis.get("description", "")

    # Build special attributes
    special_attrs = []
    if ident.get("rookie_card"):
        special_attrs.append("🌟 RC")
    if ident.get("autograph"):
        special_attrs.append("✍️ AUTO")
    if ident.get("memorabilia"):
        special_attrs.append(f"👕 {escape_md(ident.get('memorabilia'))}")
    if ident.get("serial_numbered"):
        special_attrs.append(f"🔢 {escape_md(ident.get('serial_numbered'))}")

    special_line = " • ".join(special_attrs) if special_attrs else ""

    # Condition emoji
    grade = str(condition.get("estimated_grade", "?"))
    if grade in ["10", "9"]:
        grade_emoji = "🟢"
    elif grade in ["8", "7"]:
        grade_emoji = "🟡"
    else:
        grade_emoji = "🔴"

    # Confidence emoji
    id_conf = confidence.get("identification_confidence", "Medium")
    conf_emoji = "🟢" if id_conf == "High" else "🟡" if id_conf == "Medium" else "🔴"

    result = f"""
🔷 *VAULTY CARD ANALYSIS* 🔮
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*🎴 IDENTIFICATION*

*Category:* {escape_md(ident.get('sport_category', 'Unknown'))}
*Player/Character:* {escape_md(ident.get('player_character', 'Unknown'))}
*Team:* {escape_md(ident.get('team', 'N/A'))}
*Year:* {escape_md(ident.get('year', 'Unknown'))}
*Manufacturer:* {escape_md(ident.get('manufacturer', 'Unknown'))}
*Set:* {escape_md(ident.get('set_name', 'Unknown'))}
*Card \\#:* {escape_md(ident.get('card_number', 'Unknown'))}
*Parallel/Subset:* {escape_md(ident.get('subset_parallel', 'Base'))}
"""

    if special_line:
        result += f"\n*Special:* {special_line}\n"

    result += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*📋 CONDITION ASSESSMENT*

{grade_emoji} *Estimated Grade:* PSA {escape_md(grade)}
• Centering: {escape_md(condition.get('centering', 'N/A'))}
• Corners: {escape_md(condition.get('corners', 'N/A'))}
• Edges: {escape_md(condition.get('edges', 'N/A'))}
• Surface: {escape_md(condition.get('surface', 'N/A'))}
"""

    flaws = condition.get("notable_flaws", [])
    if flaws and flaws != ["None"] and len(flaws) > 0:
        flaws_text = ", ".join([escape_md(f) for f in flaws])
        result += f"• Flaws: _{flaws_text}_\n"

    result += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    # Use verified pricing system if available
    if price_estimates and PRICING_AVAILABLE:
        result += price_formatter.format_full_price_section(price_estimates, ident)
    else:
        # Fallback to AI estimates with warning
        trend = ai_values.get("value_trend", "Stable")
        trend_emoji = "📈" if trend == "Rising" else "📉" if trend == "Declining" else "➡️"

        def format_price(value) -> str:
            try:
                num = float(value) if value else 0
                if num >= 1000:
                    return f"${num:,.0f}".replace(",", "\\,")
                elif num >= 1:
                    return f"${num:.0f}"
                else:
                    return f"${num:.2f}"
            except (ValueError, TypeError):
                return escape_md(str(value))

        result += f"""*💰 MARKET VALUES \\(USD\\)*

⚠️ *AI Estimates \\- Always verify on eBay Sold\\!*

*RAW \\(Ungraded\\):*
└ {format_price(ai_values.get('raw_low', 0))} \\- {format_price(ai_values.get('raw_high', 0))}

*Graded:*
🏆 PSA 10: ~{format_price(ai_values.get('psa_10', 0))}
🥇 PSA 9: ~{format_price(ai_values.get('psa_9', 0))}
🥈 PSA 8: ~{format_price(ai_values.get('psa_8', 0))}

{trend_emoji} *Trend:* {escape_md(trend)}

🔍 *Verify prices on eBay Sold listings\\!*
"""

    result += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{conf_emoji} *ID Confidence:* {escape_md(id_conf)}
"""

    if desc:
        result += f"\n📄 _{escape_md(desc)}_\n"

    if confidence.get("notes"):
        result += f"\n⚠️ _{escape_md(confidence.get('notes'))}_\n"

    result += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_Powered by Vaulty Protocol × Claude Vision_
"""

    return result


async def analyze_card_image(image_data: bytes, media_type: str = "image/jpeg") -> dict:
    """Analyze a card image using Claude Vision API."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    client = anthropic.Anthropic(api_key=api_key)
    base64_image = base64.standard_b64encode(image_data).decode("utf-8")

    # Updated prompt - focus on identification, let pricing system handle values
    analysis_prompt = """You are an expert trading card analyst. Analyze this trading card image and provide detailed identification.

IMPORTANT: Respond ONLY with a valid JSON object, no additional text or markdown formatting.

Focus on ACCURATE IDENTIFICATION. For prices, provide rough estimates only - they will be refined by our pricing database.

Return this exact JSON structure:
{
    "identification": {
        "sport_category": "Sport or category (Baseball, Basketball, Football, Pokemon, MTG, Yu-Gi-Oh, etc.)",
        "player_character": "Player name or character name - BE PRECISE",
        "team": "Team name if applicable, or null",
        "year": "Year of the card (number only, e.g., 2003)",
        "manufacturer": "Card manufacturer (Topps, Panini, Upper Deck, WOTC, etc.)",
        "set_name": "EXACT name of the card set",
        "card_number": "Card number in the set",
        "subset_parallel": "Subset or parallel name if applicable (Base, Rookie, Refractor, Silver Prizm, etc.)",
        "serial_numbered": "Serial numbering if visible (e.g., '/99', '/25'), or null",
        "rookie_card": true/false,
        "autograph": true/false,
        "memorabilia": "Type of memorabilia if present (jersey, patch, etc.), or null"
    },
    "condition_assessment": {
        "estimated_grade": "Estimated PSA grade 1-10 (number only)",
        "centering": "Poor/Fair/Good/Excellent",
        "corners": "Poor/Fair/Good/Excellent",
        "edges": "Poor/Fair/Good/Excellent",
        "surface": "Poor/Fair/Good/Excellent",
        "notable_flaws": ["List any visible flaws"]
    },
    "market_values": {
        "raw_low": 0,
        "raw_mid": 0,
        "raw_high": 0,
        "psa_10": 0,
        "psa_9": 0,
        "psa_8": 0,
        "value_trend": "Rising/Stable/Declining",
        "market_notes": "Brief note about the card's market"
    },
    "confidence": {
        "identification_confidence": "High/Medium/Low",
        "value_confidence": "Low",
        "notes": "Any uncertainty about identification"
    },
    "description": "Brief 1-2 sentence description of the card"
}

IMPORTANT:
- Be VERY precise with player names, set names, and years
- If uncertain about identification, say so in the notes
- For values, only provide rough ballpark estimates - our database will refine them
- All numeric values should be numbers only (no $ or commas)"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": base64_image,
                        },
                    },
                    {"type": "text", "text": analysis_prompt}
                ],
            }
        ],
    )

    response_text = message.content[0].text

    try:
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        return json.loads(response_text.strip())
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        raise ValueError("Failed to parse API response")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    await update.message.reply_text(get_welcome_message(), parse_mode="MarkdownV2")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command."""
    help_text = """
🔷 *VAULTY CARD ANALYZER \\- HELP* 🔮
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*Commands:*
/start \\- Welcome message
/help \\- Show this help
/about \\- About the bot
/stats \\- Database statistics

*How to analyze a card:*
1\\. Take a clear photo of your card
2\\. Send the photo to this chat
3\\. Wait for the AI analysis

*Understanding confidence levels:*
🟢 HIGH \\- Verified from real sales
🟡 MEDIUM \\- Algorithm estimate
🟠 LOW \\- Rough estimate
🔴 N/A \\- Check eBay Sold

*Tips for best results:*
• Use good lighting
• Capture the full card
• Avoid glare and reflections
• Higher resolution \\= better ID

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_Powered by Vaulty Protocol × Claude Vision_
"""
    await update.message.reply_text(help_text, parse_mode="MarkdownV2")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /about command."""
    about_text = """
🔷 *ABOUT VAULTY CARD ANALYZER* 🔮
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*Version:* 2\\.0\\.0

This bot uses advanced AI vision technology combined with a verified price database for accurate card analysis\\.

🏀 Sports Cards \\(Basketball, Football, Baseball\\)
🎴 TCGs \\(Pokemon, Magic, Yu\\-Gi\\-Oh\\!\\)
⚽ Soccer Cards

*Price Accuracy:*
• Verified database for popular cards
• Algorithm estimates for others
• Always shows confidence level

*Disclaimer:*
Prices are estimates\\. Always verify on eBay Sold before buying/selling\\.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_© 2024 Vaulty Protocol_
"""
    await update.message.reply_text(about_text, parse_mode="MarkdownV2")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /stats command."""
    if not PRICING_AVAILABLE or not db_manager:
        await update.message.reply_text(
            "📊 Database not available\\.",
            parse_mode="MarkdownV2"
        )
        return

    stats = db_manager.get_stats()

    categories_text = "\n".join([
        f"• {escape_md(cat)}: {count}"
        for cat, count in stats.get("categories", {}).items()
    ])

    stats_text = f"""
📊 *DATABASE STATISTICS*
━━━━━━━━━━━━━━━━━━━━━━

*Verified Cards:* {stats.get('total_cards', 0)}
*Price Entries:* {stats.get('total_price_entries', 0)}

*Categories:*
{categories_text}

━━━━━━━━━━━━━━━━━━━━━━
_Growing daily\\!_
"""
    await update.message.reply_text(stats_text, parse_mode="MarkdownV2")


# ==================== ADMIN COMMANDS ====================

async def addprice_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to add a verified price."""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Admin only command\\.", parse_mode="MarkdownV2")
        return

    if not PRICING_AVAILABLE or not db_manager:
        await update.message.reply_text("❌ Pricing system not available\\.", parse_mode="MarkdownV2")
        return

    # Parse arguments: /addprice card_id grade min max
    args = context.args
    if len(args) < 4:
        await update.message.reply_text(
            "Usage: `/addprice card_id grade min_price max_price`\n\n"
            "Example: `/addprice 2018_prizm_luka_doncic PSA\\_10 350 500`",
            parse_mode="MarkdownV2"
        )
        return

    card_id = args[0]
    grade = args[1].replace("_", " ")
    try:
        price_min = float(args[2])
        price_max = float(args[3])
    except ValueError:
        await update.message.reply_text("❌ Invalid price values\\.", parse_mode="MarkdownV2")
        return

    # Check if card exists
    if card_id in db_manager.verified_prices:
        db_manager.update_price(card_id, grade, price_min, price_max)
        await update.message.reply_text(
            f"✅ Updated price for `{escape_md(card_id)}`\n"
            f"Grade: {escape_md(grade)}\n"
            f"Price: ${price_min} \\- ${price_max}",
            parse_mode="MarkdownV2"
        )
    else:
        await update.message.reply_text(
            f"❌ Card `{escape_md(card_id)}` not found in database\\.\n"
            "Use /newcard to add a new card first\\.",
            parse_mode="MarkdownV2"
        )


async def checkprice_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to check prices in database."""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Admin only command\\.", parse_mode="MarkdownV2")
        return

    if not PRICING_AVAILABLE or not db_manager:
        await update.message.reply_text("❌ Pricing system not available\\.", parse_mode="MarkdownV2")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "Usage: `/checkprice card_id` or `/checkprice search_query`",
            parse_mode="MarkdownV2"
        )
        return

    query = " ".join(args)

    # Try exact match first
    if query in db_manager.verified_prices:
        card = db_manager.verified_prices[query]
        result = price_formatter.format_admin_price_entry(query, card)
        await update.message.reply_text(result, parse_mode="MarkdownV2")
        return

    # Search
    results = db_manager.search_cards(query, limit=5)
    if not results:
        await update.message.reply_text(f"No cards found matching `{escape_md(query)}`", parse_mode="MarkdownV2")
        return

    response = "*Search Results:*\n\n"
    for card_id, card in results:
        response += f"• `{escape_md(card_id)}`\n  {escape_md(card.get('name', 'N/A'))}\n\n"

    await update.message.reply_text(response, parse_mode="MarkdownV2")


async def oldprices_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to list stale prices."""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Admin only command\\.", parse_mode="MarkdownV2")
        return

    if not PRICING_AVAILABLE or not db_manager:
        await update.message.reply_text("❌ Pricing system not available\\.", parse_mode="MarkdownV2")
        return

    stale = db_manager.get_stale_prices(days=90)

    if not stale:
        await update.message.reply_text("✅ All prices are up to date\\!", parse_mode="MarkdownV2")
        return

    response = f"*⚠️ Stale Prices \\(\\>90 days\\):* {len(stale)} entries\n\n"
    for card_id, name, grade, last_ver in stale[:20]:  # Limit to 20
        response += f"• `{escape_md(card_id[:30])}`\n  {escape_md(grade)} \\- last: {escape_md(last_ver)}\n"

    if len(stale) > 20:
        response += f"\n_\\.\\.\\. and {len(stale) - 20} more_"

    await update.message.reply_text(response, parse_mode="MarkdownV2")


async def exportdb_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to export database."""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Admin only command\\.", parse_mode="MarkdownV2")
        return

    if not PRICING_AVAILABLE or not db_manager:
        await update.message.reply_text("❌ Pricing system not available\\.", parse_mode="MarkdownV2")
        return

    export_data = db_manager.export_database()
    json_str = json.dumps(export_data, indent=2, ensure_ascii=False)

    # Send as document
    from io import BytesIO
    file_bytes = BytesIO(json_str.encode('utf-8'))
    file_bytes.name = "vaulty_database_export.json"

    await update.message.reply_document(
        document=file_bytes,
        caption="📦 Database export"
    )


# ==================== PHOTO HANDLERS ====================

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming photos."""
    user = update.effective_user
    logger.info(f"Received photo from user {user.id} ({user.username})")

    status_message = await update.message.reply_text(
        get_analyzing_message(),
        parse_mode="MarkdownV2"
    )

    try:
        # Get the largest photo
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)

        # Download photo to memory
        photo_bytes = BytesIO()
        await file.download_to_memory(photo_bytes)
        photo_data = photo_bytes.getvalue()

        # Analyze the card with AI
        analysis = await analyze_card_image(photo_data, "image/jpeg")

        # Get price estimates from our database
        price_estimates = None
        if PRICING_AVAILABLE and price_estimator:
            ident = analysis.get("identification", {})
            price_estimates = price_estimator.estimate_all_grades(ident)

        # Format and send result
        result_text = format_analysis_result(analysis, price_estimates)

        await status_message.delete()
        await update.message.reply_text(result_text, parse_mode="MarkdownV2")

        logger.info(f"Successfully analyzed card for user {user.id}")

    except ValueError as e:
        await status_message.edit_text(
            f"❌ *Error:* {escape_md(str(e))}\n\nPlease try again\\.",
            parse_mode="MarkdownV2"
        )
        logger.error(f"ValueError for user {user.id}: {e}")

    except anthropic.APIError as e:
        await status_message.edit_text(
            "❌ *API Error*\n\nAI service temporarily unavailable\\. Please try again later\\.",
            parse_mode="MarkdownV2"
        )
        logger.error(f"API error for user {user.id}: {e}")

    except Exception as e:
        await status_message.edit_text(
            "❌ *Unexpected Error*\n\nSomething went wrong\\. Please try again\\.",
            parse_mode="MarkdownV2"
        )
        logger.error(f"Unexpected error for user {user.id}: {e}", exc_info=True)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle documents (in case user sends image as file)."""
    document = update.message.document

    if document.mime_type and document.mime_type.startswith("image/"):
        user = update.effective_user
        logger.info(f"Received document image from user {user.id}")

        status_message = await update.message.reply_text(
            get_analyzing_message(),
            parse_mode="MarkdownV2"
        )

        try:
            file = await context.bot.get_file(document.file_id)
            photo_bytes = BytesIO()
            await file.download_to_memory(photo_bytes)
            photo_data = photo_bytes.getvalue()

            analysis = await analyze_card_image(photo_data, document.mime_type)

            price_estimates = None
            if PRICING_AVAILABLE and price_estimator:
                ident = analysis.get("identification", {})
                price_estimates = price_estimator.estimate_all_grades(ident)

            result_text = format_analysis_result(analysis, price_estimates)

            await status_message.delete()
            await update.message.reply_text(result_text, parse_mode="MarkdownV2")

        except Exception as e:
            await status_message.edit_text(
                f"❌ *Error analyzing image*\n\n_{escape_md(str(e))}_",
                parse_mode="MarkdownV2"
            )
            logger.error(f"Error processing document: {e}")
    else:
        await update.message.reply_text(
            "⚠️ Please send an image file \\(JPEG, PNG, WebP\\)\\.",
            parse_mode="MarkdownV2"
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages."""
    await update.message.reply_text(
        "📸 Please send me a *photo* of your trading card to analyze\\!\n\nUse /help for more information\\.",
        parse_mode="MarkdownV2"
    )


def main() -> None:
    """Start the bot."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        print("❌ Error: TELEGRAM_BOT_TOKEN environment variable not set")
        sys.exit(1)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    print("""
╔══════════════════════════════════════════════════════════════╗
║              VAULTY CARD ANALYZER - TELEGRAM BOT              ║
║                   Powered by Claude Vision                    ║
║                  v2.0 - Verified Price Database               ║
╚══════════════════════════════════════════════════════════════╝
    """)

    if PRICING_AVAILABLE:
        stats = db_manager.get_stats()
        print(f"📊 Loaded {stats['total_cards']} cards with {stats['total_price_entries']} verified prices")
    else:
        print("⚠️  Pricing system not available - using AI estimates only")

    print("🚀 Starting bot...")

    application = Application.builder().token(token).build()

    # Public commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("stats", stats_command))

    # Admin commands
    application.add_handler(CommandHandler("addprice", addprice_command))
    application.add_handler(CommandHandler("checkprice", checkprice_command))
    application.add_handler(CommandHandler("oldprices", oldprices_command))
    application.add_handler(CommandHandler("exportdb", exportdb_command))

    # Message handlers
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("✅ Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
