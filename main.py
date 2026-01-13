#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      VAULTY CARD ANALYZER - TELEGRAM BOT                      ║
║                    Trading Card Recognition & Valuation                       ║
║                         Powered by Claude Vision                              ║
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

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Vaulty Protocol Brand Colors (for reference in messages)
VAULTY_CYAN = "🔷"
VAULTY_MAGENTA = "🔮"
VAULTY_ACCENT = "💎"


def get_welcome_message() -> str:
    """Return the welcome message."""
    return """
🔷 *VAULTY CARD ANALYZER* 🔮
━━━━━━━━━━━━━━━━━━━━━━━━━━

Welcome to the AI-powered trading card analyzer\\!

📸 *How to use:*
Simply send me a photo of your trading card and I'll analyze it for you\\.

💎 *I can identify:*
• Player/Character name
• Card set and year
• Card number and parallels
• Rookie cards, autos, memorabilia

📊 *I'll estimate values for:*
• RAW \\(ungraded\\)
• PSA 10 \\(Gem Mint\\)
• PSA 9 \\(Mint\\)
• PSA 8 \\(NM\\-MT\\)

━━━━━━━━━━━━━━━━━━━━━━━━━━
_Powered by Vaulty Protocol × Claude Vision_
"""


def get_analyzing_message() -> str:
    """Return the analyzing status message."""
    return "🔮 *Analyzing your card with AI vision\\.\\.\\.*\n\n_This may take a few seconds\\._"


def format_analysis_result(analysis: dict) -> str:
    """Format the analysis result for Telegram with MarkdownV2."""
    ident = analysis.get("identification", {})
    condition = analysis.get("condition_assessment", {})
    values = analysis.get("market_values", {})
    confidence = analysis.get("confidence", {})
    desc = analysis.get("description", "")

    def escape_md(text) -> str:
        """Escape special characters for MarkdownV2."""
        if text is None:
            return "N/A"
        text = str(text)
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text

    def format_price(value) -> str:
        """Format price value."""
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

    # Trend emoji
    trend = values.get("value_trend", "Stable")
    trend_emoji = "📈" if trend == "Rising" else "📉" if trend == "Declining" else "➡️"

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

    result += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*💰 MARKET VALUES \\(USD\\)*

*RAW \\(Ungraded\\):*
└ {format_price(values.get('raw_low', 0))} \\- {format_price(values.get('raw_high', 0))}
└ Mid: *{format_price(values.get('raw_mid', 0))}*

*Graded:*
🏆 PSA 10: *{format_price(values.get('psa_10', 0))}*
🥇 PSA 9: {format_price(values.get('psa_9', 0))}
🥈 PSA 8: {format_price(values.get('psa_8', 0))}

{trend_emoji} *Trend:* {escape_md(trend)}
"""

    if values.get("market_notes"):
        result += f"📝 _{escape_md(values.get('market_notes'))}_\n"

    result += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{conf_emoji} *Confidence:* {escape_md(id_conf)}
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

    # Encode image to base64
    base64_image = base64.standard_b64encode(image_data).decode("utf-8")

    analysis_prompt = """You are an expert trading card analyst and appraiser. Analyze this trading card image and provide detailed information.

IMPORTANT: Respond ONLY with a valid JSON object, no additional text or markdown formatting.

Analyze the card and return this exact JSON structure:
{
    "identification": {
        "sport_category": "Sport or category (Baseball, Basketball, Football, Pokemon, MTG, Yu-Gi-Oh, etc.)",
        "player_character": "Player name or character name",
        "team": "Team name if applicable, or null",
        "year": "Year of the card",
        "manufacturer": "Card manufacturer (Topps, Panini, Upper Deck, WOTC, etc.)",
        "set_name": "Name of the card set",
        "card_number": "Card number in the set",
        "subset_parallel": "Subset or parallel name if applicable (Base, Rookie, Refractor, Holo, etc.)",
        "serial_numbered": "Serial numbering if visible (e.g., '/99', '/25'), or null",
        "rookie_card": true/false,
        "autograph": true/false,
        "memorabilia": "Type of memorabilia if present (jersey, patch, etc.), or null"
    },
    "condition_assessment": {
        "estimated_grade": "Estimated PSA grade 1-10",
        "centering": "Poor/Fair/Good/Excellent",
        "corners": "Poor/Fair/Good/Excellent",
        "edges": "Poor/Fair/Good/Excellent",
        "surface": "Poor/Fair/Good/Excellent",
        "notable_flaws": ["List any visible flaws"]
    },
    "market_values": {
        "raw_low": "Low estimate for ungraded card in USD",
        "raw_mid": "Mid estimate for ungraded card in USD",
        "raw_high": "High estimate for ungraded card in USD",
        "psa_10": "Estimated PSA 10 value in USD",
        "psa_9": "Estimated PSA 9 value in USD",
        "psa_8": "Estimated PSA 8 value in USD",
        "value_trend": "Rising/Stable/Declining",
        "market_notes": "Any relevant market information"
    },
    "confidence": {
        "identification_confidence": "High/Medium/Low",
        "value_confidence": "High/Medium/Low",
        "notes": "Any uncertainty or additional notes"
    },
    "description": "A brief 1-2 sentence description of the card"
}

If you cannot identify certain details, use "Unknown" for strings and null for optional fields.
For values, provide realistic market estimates based on your knowledge.
All USD values should be numbers only (no $ symbol or commas)."""

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
                    {
                        "type": "text",
                        "text": analysis_prompt
                    }
                ],
            }
        ],
    )

    response_text = message.content[0].text

    # Parse JSON from response
    try:
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        return json.loads(response_text.strip())
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        raise ValueError(f"Failed to parse API response")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    await update.message.reply_text(
        get_welcome_message(),
        parse_mode="MarkdownV2"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command."""
    help_text = """
🔷 *VAULTY CARD ANALYZER \\- HELP* 🔮
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*Commands:*
/start \\- Welcome message
/help \\- Show this help
/about \\- About the bot

*How to analyze a card:*
1\\. Take a clear photo of your card
2\\. Send the photo to this chat
3\\. Wait for the AI analysis

*Tips for best results:*
• Use good lighting
• Capture the full card
• Avoid glare and reflections
• Higher resolution \\= better results

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_Powered by Vaulty Protocol × Claude Vision_
"""
    await update.message.reply_text(help_text, parse_mode="MarkdownV2")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /about command."""
    about_text = """
🔷 *ABOUT VAULTY CARD ANALYZER* 🔮
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*Version:* 1\\.0\\.0

This bot uses advanced AI vision technology to analyze trading cards from various categories:

🏀 Sports Cards \\(Baseball, Basketball, Football, Hockey\\)
🎴 TCGs \\(Pokemon, Magic: The Gathering, Yu\\-Gi\\-Oh\\!\\)
🎮 Gaming Cards
🎬 Entertainment Cards

*Powered by:*
• Claude Vision AI
• Vaulty Protocol

*Disclaimer:*
Values are estimates based on AI analysis\\. Always verify with current market data before making purchasing decisions\\.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_© 2024 Vaulty Protocol_
"""
    await update.message.reply_text(about_text, parse_mode="MarkdownV2")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming photos."""
    user = update.effective_user
    logger.info(f"Received photo from user {user.id} ({user.username})")

    # Send analyzing message
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

        # Analyze the card
        analysis = await analyze_card_image(photo_data, "image/jpeg")

        # Format and send result
        result_text = format_analysis_result(analysis)

        # Delete status message
        await status_message.delete()

        # Send result
        await update.message.reply_text(
            result_text,
            parse_mode="MarkdownV2"
        )

        logger.info(f"Successfully analyzed card for user {user.id}")

    except ValueError as e:
        await status_message.edit_text(
            f"❌ *Error:* {str(e)}\n\nPlease try again or contact support\\.",
            parse_mode="MarkdownV2"
        )
        logger.error(f"ValueError for user {user.id}: {e}")

    except anthropic.APIError as e:
        await status_message.edit_text(
            "❌ *API Error*\n\nThe AI service is temporarily unavailable\\. Please try again later\\.",
            parse_mode="MarkdownV2"
        )
        logger.error(f"API error for user {user.id}: {e}")

    except Exception as e:
        await status_message.edit_text(
            "❌ *Unexpected Error*\n\nSomething went wrong\\. Please try again\\.",
            parse_mode="MarkdownV2"
        )
        logger.error(f"Unexpected error for user {user.id}: {e}")


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
            result_text = format_analysis_result(analysis)

            await status_message.delete()
            await update.message.reply_text(result_text, parse_mode="MarkdownV2")

        except Exception as e:
            await status_message.edit_text(
                f"❌ *Error analyzing image*\n\n_{str(e)}_",
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
    # Get token from environment
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        print("❌ Error: TELEGRAM_BOT_TOKEN environment variable not set")
        sys.exit(1)

    # Check for Anthropic API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    print("""
╔══════════════════════════════════════════════════════════════╗
║              VAULTY CARD ANALYZER - TELEGRAM BOT              ║
║                   Powered by Claude Vision                    ║
╚══════════════════════════════════════════════════════════════╝
    """)
    print("🚀 Starting bot...")

    # Create application
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Start polling
    print("✅ Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
