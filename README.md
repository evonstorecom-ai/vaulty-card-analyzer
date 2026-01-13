# Vaulty Card Analyzer

AI-powered trading card recognition and valuation tool using Claude Vision.

## Features

- Card identification (player, set, year, card number)
- Condition assessment (centering, corners, edges, surface)
- Market value estimation (RAW and PSA graded)
- Beautiful terminal output with Vaulty Protocol branding
- JSON export support
- **Telegram Bot** for mobile access

## Installation

```bash
pip install -r requirements.txt
```

## CLI Usage

```bash
# Set your API key
export ANTHROPIC_API_KEY=your_key_here

# Analyze a card
python vaulty_card_analyzer.py card.jpg

# Export to JSON
python vaulty_card_analyzer.py card.png --json output.json

# Quiet mode
python vaulty_card_analyzer.py card.webp -q
```

## Telegram Bot

### Local Development

```bash
export ANTHROPIC_API_KEY=your_anthropic_key
export TELEGRAM_BOT_TOKEN=your_telegram_bot_token

python telegram_bot.py
```

### Railway Deployment

1. Create a new project on [Railway](https://railway.app)
2. Connect your GitHub repository
3. Add environment variables:
   - `ANTHROPIC_API_KEY` - Your Anthropic API key
   - `TELEGRAM_BOT_TOKEN` - Your Telegram bot token (from @BotFather)
4. Deploy!

The `Procfile` is already configured for Railway.

### Bot Commands

- `/start` - Welcome message
- `/help` - Help information
- `/about` - About the bot

Simply send a photo of your trading card to get instant analysis!

## Supported Formats

JPEG, PNG, GIF, WebP

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (required) |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token (required for bot) |

## License

Vaulty Protocol
