#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         VAULTY CARD ANALYZER                                  ║
║                    Trading Card Recognition & Valuation                       ║
║                         Powered by Claude Vision                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

A powerful CLI tool for analyzing collectible trading cards using AI vision.
Identifies cards and provides market value estimates for RAW and graded conditions.
"""

import argparse
import base64
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import anthropic
except ImportError:
    print("\n❌ Error: anthropic package not installed")
    print("   Run: pip install anthropic")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box
except ImportError:
    print("\n❌ Error: rich package not installed")
    print("   Run: pip install rich")
    sys.exit(1)


# Vaulty Protocol Brand Colors
VAULTY_CYAN = "#00D4FF"
VAULTY_MAGENTA = "#FF00FF"
VAULTY_DARK = "#1A1A2E"
VAULTY_ACCENT = "#00FFB3"

console = Console()


def get_vaulty_banner() -> str:
    """Return the Vaulty Protocol ASCII banner."""
    return """
[bold #00D4FF]██╗   ██╗ █████╗ ██╗   ██╗██╗  ████████╗██╗   ██╗[/bold #00D4FF]
[bold #00D4FF]██║   ██║██╔══██╗██║   ██║██║  ╚══██╔══╝╚██╗ ██╔╝[/bold #00D4FF]
[bold #FF00FF]██║   ██║███████║██║   ██║██║     ██║    ╚████╔╝ [/bold #FF00FF]
[bold #FF00FF]╚██╗ ██╔╝██╔══██║██║   ██║██║     ██║     ╚██╔╝  [/bold #FF00FF]
[bold #00D4FF] ╚████╔╝ ██║  ██║╚██████╔╝███████╗██║      ██║   [/bold #00D4FF]
[bold #00D4FF]  ╚═══╝  ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝      ╚═╝   [/bold #00D4FF]
[dim #FF00FF]━━━━━━━━━━━ CARD ANALYZER ━━━━━━━━━━━[/dim #FF00FF]
"""


def load_image(image_path: str) -> tuple[str, str]:
    """
    Load and encode an image file to base64.

    Args:
        image_path: Path to the image file

    Returns:
        Tuple of (base64_data, media_type)
    """
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Determine media type
    suffix = path.suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }

    media_type = media_types.get(suffix)
    if not media_type:
        raise ValueError(f"Unsupported image format: {suffix}")

    # Read and encode
    with open(path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    return image_data, media_type


def analyze_card(image_path: str, api_key: Optional[str] = None) -> dict:
    """
    Analyze a trading card image using Claude Vision API.

    Args:
        image_path: Path to the card image
        api_key: Anthropic API key (uses env var if not provided)

    Returns:
        Dictionary containing card analysis results
    """
    # Initialize client
    client = anthropic.Anthropic(api_key=api_key)

    # Load image
    image_data, media_type = load_image(image_path)

    # Craft the analysis prompt
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
For values, provide realistic market estimates based on your knowledge up to your training cutoff.
All USD values should be numbers only (no $ symbol or commas)."""

    # Make API call
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
                            "data": image_data,
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

    # Parse response
    response_text = message.content[0].text

    # Try to extract JSON from response
    try:
        # Handle potential markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        result = json.loads(response_text.strip())
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse API response as JSON: {e}\nResponse: {response_text}")

    # Add metadata
    result["metadata"] = {
        "analyzed_at": datetime.now().isoformat(),
        "image_path": str(Path(image_path).absolute()),
        "analyzer_version": "1.0.0"
    }

    return result


def display_results(analysis: dict) -> None:
    """Display analysis results with Vaulty Protocol styling."""

    console.print(get_vaulty_banner())

    ident = analysis.get("identification", {})
    condition = analysis.get("condition_assessment", {})
    values = analysis.get("market_values", {})
    confidence = analysis.get("confidence", {})

    # Card Identification Panel
    id_table = Table(show_header=False, box=None, padding=(0, 2))
    id_table.add_column("Field", style=f"bold {VAULTY_CYAN}")
    id_table.add_column("Value", style="white")

    id_table.add_row("Category", str(ident.get("sport_category", "Unknown")))
    id_table.add_row("Player/Character", str(ident.get("player_character", "Unknown")))
    if ident.get("team"):
        id_table.add_row("Team", str(ident.get("team")))
    id_table.add_row("Year", str(ident.get("year", "Unknown")))
    id_table.add_row("Manufacturer", str(ident.get("manufacturer", "Unknown")))
    id_table.add_row("Set", str(ident.get("set_name", "Unknown")))
    id_table.add_row("Card #", str(ident.get("card_number", "Unknown")))
    if ident.get("subset_parallel"):
        id_table.add_row("Parallel/Subset", str(ident.get("subset_parallel")))
    if ident.get("serial_numbered"):
        id_table.add_row("Serial #", str(ident.get("serial_numbered")))

    # Special attributes
    special = []
    if ident.get("rookie_card"):
        special.append("[bold yellow]RC[/bold yellow]")
    if ident.get("autograph"):
        special.append("[bold gold1]AUTO[/bold gold1]")
    if ident.get("memorabilia"):
        special.append(f"[bold green]{ident.get('memorabilia').upper()}[/bold green]")
    if special:
        id_table.add_row("Special", " ".join(special))

    console.print(Panel(
        id_table,
        title=f"[bold {VAULTY_CYAN}]CARD IDENTIFICATION[/bold {VAULTY_CYAN}]",
        border_style=VAULTY_CYAN,
        box=box.DOUBLE_EDGE
    ))

    # Condition Assessment Panel
    cond_table = Table(show_header=False, box=None, padding=(0, 2))
    cond_table.add_column("Aspect", style=f"bold {VAULTY_MAGENTA}")
    cond_table.add_column("Rating", style="white")

    grade = condition.get("estimated_grade", "N/A")
    grade_color = VAULTY_ACCENT if str(grade) in ["9", "10"] else "yellow" if str(grade) in ["7", "8"] else "red"
    cond_table.add_row("Est. Grade", f"[bold {grade_color}]PSA {grade}[/bold {grade_color}]")
    cond_table.add_row("Centering", get_rating_display(condition.get("centering", "N/A")))
    cond_table.add_row("Corners", get_rating_display(condition.get("corners", "N/A")))
    cond_table.add_row("Edges", get_rating_display(condition.get("edges", "N/A")))
    cond_table.add_row("Surface", get_rating_display(condition.get("surface", "N/A")))

    flaws = condition.get("notable_flaws", [])
    if flaws and flaws != ["None"]:
        cond_table.add_row("Flaws", "[dim]" + ", ".join(flaws) + "[/dim]")

    console.print(Panel(
        cond_table,
        title=f"[bold {VAULTY_MAGENTA}]CONDITION ASSESSMENT[/bold {VAULTY_MAGENTA}]",
        border_style=VAULTY_MAGENTA,
        box=box.DOUBLE_EDGE
    ))

    # Market Values Panel
    value_table = Table(box=box.SIMPLE_HEAD, padding=(0, 2))
    value_table.add_column("Condition", style=f"bold {VAULTY_CYAN}", justify="left")
    value_table.add_column("Value", style=f"bold {VAULTY_ACCENT}", justify="right")

    # RAW values
    raw_low = values.get("raw_low", 0)
    raw_mid = values.get("raw_mid", 0)
    raw_high = values.get("raw_high", 0)

    value_table.add_row(
        "RAW (Ungraded)",
        f"${format_price(raw_low)} - ${format_price(raw_high)}"
    )
    value_table.add_row("  └─ Mid Estimate", f"[bold]${format_price(raw_mid)}[/bold]")
    value_table.add_row("", "")

    # Graded values
    psa_10 = values.get("psa_10", 0)
    psa_9 = values.get("psa_9", 0)
    psa_8 = values.get("psa_8", 0)

    value_table.add_row("[bold yellow]PSA 10 (Gem Mint)[/bold yellow]", f"[bold yellow]${format_price(psa_10)}[/bold yellow]")
    value_table.add_row("PSA 9 (Mint)", f"${format_price(psa_9)}")
    value_table.add_row("PSA 8 (NM-MT)", f"${format_price(psa_8)}")

    # Trend
    trend = values.get("value_trend", "Stable")
    trend_icon = "📈" if trend == "Rising" else "📉" if trend == "Declining" else "➡️"
    value_table.add_row("", "")
    value_table.add_row("Market Trend", f"{trend_icon} {trend}")

    if values.get("market_notes"):
        value_table.add_row("Notes", f"[dim]{values.get('market_notes')}[/dim]")

    console.print(Panel(
        value_table,
        title=f"[bold {VAULTY_ACCENT}]MARKET VALUES (USD)[/bold {VAULTY_ACCENT}]",
        border_style=VAULTY_ACCENT,
        box=box.DOUBLE_EDGE
    ))

    # Confidence & Description
    conf_level = confidence.get("identification_confidence", "Medium")
    val_conf = confidence.get("value_confidence", "Medium")
    desc = analysis.get("description", "")

    conf_text = Text()
    conf_text.append("ID Confidence: ", style=f"bold {VAULTY_CYAN}")
    conf_text.append(get_confidence_display(conf_level))
    conf_text.append("  |  Value Confidence: ", style=f"bold {VAULTY_CYAN}")
    conf_text.append(get_confidence_display(val_conf))

    if desc:
        conf_text.append(f"\n\n{desc}", style="italic")

    if confidence.get("notes"):
        conf_text.append(f"\n\n[dim]Note: {confidence.get('notes')}[/dim]")

    console.print(Panel(
        conf_text,
        title=f"[bold {VAULTY_MAGENTA}]ANALYSIS SUMMARY[/bold {VAULTY_MAGENTA}]",
        border_style=VAULTY_MAGENTA,
        box=box.ROUNDED
    ))

    # Footer
    console.print(f"\n[dim {VAULTY_CYAN}]━━━ Powered by Vaulty Protocol × Claude Vision ━━━[/dim {VAULTY_CYAN}]")
    console.print(f"[dim]Analysis completed at: {analysis.get('metadata', {}).get('analyzed_at', 'N/A')}[/dim]\n")


def get_rating_display(rating: str) -> str:
    """Convert rating to colored display."""
    rating_colors = {
        "Excellent": f"[bold {VAULTY_ACCENT}]●●●●[/bold {VAULTY_ACCENT}] Excellent",
        "Good": "[bold yellow]●●●○[/bold yellow] Good",
        "Fair": "[bold orange1]●●○○[/bold orange1] Fair",
        "Poor": "[bold red]●○○○[/bold red] Poor",
    }
    return rating_colors.get(rating, f"[dim]{rating}[/dim]")


def get_confidence_display(level: str) -> str:
    """Convert confidence level to colored display."""
    if level == "High":
        return f"[bold {VAULTY_ACCENT}]HIGH[/bold {VAULTY_ACCENT}]"
    elif level == "Medium":
        return "[bold yellow]MEDIUM[/bold yellow]"
    else:
        return "[bold red]LOW[/bold red]"


def format_price(value) -> str:
    """Format price value with proper number formatting."""
    try:
        num = float(value) if value else 0
        if num >= 1000:
            return f"{num:,.0f}"
        elif num >= 100:
            return f"{num:.0f}"
        elif num >= 1:
            return f"{num:.2f}"
        else:
            return f"{num:.2f}"
    except (ValueError, TypeError):
        return str(value)


def export_json(analysis: dict, output_path: str) -> None:
    """Export analysis results to JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    console.print(f"\n[bold {VAULTY_ACCENT}]✓ Results exported to:[/bold {VAULTY_ACCENT}] {output_path}")


def main():
    """Main entry point for the Vaulty Card Analyzer."""
    parser = argparse.ArgumentParser(
        description="Vaulty Card Analyzer - AI-powered trading card recognition and valuation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s card.jpg                    Analyze a card image
  %(prog)s card.png --json output.json Analyze and export to JSON
  %(prog)s card.webp -v                Analyze with verbose output

Supported formats: JPEG, PNG, GIF, WebP

Environment Variables:
  ANTHROPIC_API_KEY    Your Anthropic API key (required)
        """
    )

    parser.add_argument(
        "image",
        help="Path to the trading card image"
    )

    parser.add_argument(
        "--json", "-j",
        metavar="FILE",
        help="Export results to JSON file"
    )

    parser.add_argument(
        "--api-key", "-k",
        help="Anthropic API key (overrides ANTHROPIC_API_KEY env var)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show verbose output including raw API response"
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Minimal output, only show essential results"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0 - Vaulty Protocol"
    )

    args = parser.parse_args()

    # Check for API key
    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print(f"\n[bold red]Error:[/bold red] No API key provided")
        console.print(f"Set the [bold {VAULTY_CYAN}]ANTHROPIC_API_KEY[/bold {VAULTY_CYAN}] environment variable or use --api-key")
        sys.exit(1)

    # Show banner unless quiet mode
    if not args.quiet:
        console.print(get_vaulty_banner())
        console.print(f"[dim]Analyzing: {args.image}[/dim]\n")

    try:
        # Show loading spinner
        with console.status(f"[bold {VAULTY_MAGENTA}]Analyzing card with Claude Vision...[/bold {VAULTY_MAGENTA}]", spinner="dots"):
            analysis = analyze_card(args.image, api_key)

        # Display results
        if args.verbose:
            console.print(Panel(
                json.dumps(analysis, indent=2),
                title="[bold]Raw API Response[/bold]",
                border_style="dim"
            ))

        if not args.quiet:
            display_results(analysis)
        else:
            # Minimal output for quiet mode
            ident = analysis.get("identification", {})
            values = analysis.get("market_values", {})
            console.print(f"[bold]{ident.get('player_character', 'Unknown')}[/bold] - {ident.get('year', '?')} {ident.get('set_name', 'Unknown')} #{ident.get('card_number', '?')}")
            console.print(f"RAW: ${format_price(values.get('raw_mid', 0))} | PSA 10: ${format_price(values.get('psa_10', 0))}")

        # Export to JSON if requested
        if args.json:
            export_json(analysis, args.json)

    except FileNotFoundError as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except ValueError as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except anthropic.APIError as e:
        console.print(f"\n[bold red]API Error:[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Unexpected Error:[/bold red] {e}")
        if args.verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
