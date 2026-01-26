"""
Vaulty Pricing - Response Formatter
Formats price estimates for Telegram bot display
"""

from typing import Optional
from .estimator import PriceEstimate


class PriceFormatter:
    """
    Formats price estimates for display in Telegram messages.
    Uses MarkdownV2 formatting with confidence indicators.
    """

    @staticmethod
    def escape_md(text) -> str:
        """Escape special characters for Telegram MarkdownV2."""
        if text is None:
            return "N/A"
        text = str(text)
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text

    @staticmethod
    def format_price(value: Optional[float], currency: str = "USD") -> str:
        """Format a price value with currency symbol."""
        if value is None:
            return "N/A"

        symbols = {"USD": "$", "EUR": "€", "CHF": "CHF ", "GBP": "£"}
        symbol = symbols.get(currency, "$")

        if value >= 10000:
            return f"{symbol}{value:,.0f}".replace(",", "\\,")
        elif value >= 1000:
            return f"{symbol}{value:,.0f}".replace(",", "\\,")
        elif value >= 100:
            return f"{symbol}{value:.0f}"
        elif value >= 1:
            return f"{symbol}{value:.0f}"
        else:
            return f"{symbol}{value:.2f}"

    @staticmethod
    def get_confidence_emoji(confidence: float) -> str:
        """Get emoji indicator for confidence level."""
        if confidence >= 0.85:
            return "🟢"  # High confidence
        elif confidence >= 0.65:
            return "🟡"  # Medium confidence
        elif confidence >= 0.50:
            return "🟠"  # Low confidence
        else:
            return "🔴"  # Very low / unavailable

    @staticmethod
    def get_confidence_label(confidence: float) -> str:
        """Get text label for confidence level."""
        if confidence >= 0.85:
            return "HIGH"
        elif confidence >= 0.65:
            return "MEDIUM"
        elif confidence >= 0.50:
            return "LOW"
        else:
            return "UNAVAILABLE"

    def format_single_estimate(self, estimate: PriceEstimate) -> str:
        """
        Format a single price estimate for display.

        Args:
            estimate: PriceEstimate object

        Returns:
            Formatted string for Telegram
        """
        emoji = self.get_confidence_emoji(estimate.confidence)
        conf_label = self.get_confidence_label(estimate.confidence)
        conf_pct = int(estimate.confidence * 100)

        if estimate.source == "unavailable":
            return self._format_unavailable(estimate)
        elif estimate.source == "verified":
            return self._format_verified(estimate, emoji, conf_label, conf_pct)
        else:
            return self._format_algorithmic(estimate, emoji, conf_label, conf_pct)

    def _format_verified(self, estimate: PriceEstimate, emoji: str, label: str, pct: int) -> str:
        """Format verified price estimate."""
        min_p = self.format_price(estimate.min_price)
        max_p = self.format_price(estimate.max_price)
        grade = self.escape_md(estimate.grade)
        last_ver = self.escape_md(estimate.last_verified or "N/A")

        return f"""{emoji} *{grade}:* {min_p} \\- {max_p}
   └ Confidence: *{label}* \\({pct}%\\)
   └ ✅ Verified: {last_ver}"""

    def _format_algorithmic(self, estimate: PriceEstimate, emoji: str, label: str, pct: int) -> str:
        """Format algorithmically calculated estimate."""
        min_p = self.format_price(estimate.min_price)
        max_p = self.format_price(estimate.max_price)
        grade = self.escape_md(estimate.grade)

        result = f"""{emoji} *{grade}:* ~{min_p} \\- {max_p}
   └ Confidence: *{label}* \\({pct}%\\)
   └ ⚠️ Estimated \\- Verify on eBay"""

        return result

    def _format_unavailable(self, estimate: PriceEstimate) -> str:
        """Format unavailable price."""
        grade = self.escape_md(estimate.grade)
        return f"""🔴 *{grade}:* Price unavailable
   └ Insufficient data for reliable estimate"""

    def format_full_price_section(
        self,
        estimates: dict,
        card_name: str = None
    ) -> str:
        """
        Format complete price section for bot response.

        Args:
            estimates: Dict mapping grade to PriceEstimate
            card_name: Optional card name for search suggestions

        Returns:
            Complete formatted price section
        """
        lines = []

        # Header
        lines.append("💰 *MARKET VALUES \\(USD\\)*")
        lines.append("")

        # Determine primary source
        sources = [e.source for e in estimates.values() if e]
        primary_source = "verified" if "verified" in sources else "algorithm"

        if primary_source == "verified":
            lines.append("✅ *Prices from verified sales*")
        else:
            lines.append("⚠️ *Estimated prices \\- verify before buying/selling*")

        lines.append("")

        # RAW price
        if "RAW" in estimates:
            raw = estimates["RAW"]
            if raw.min_price is not None:
                lines.append(f"*Ungraded \\(RAW\\):*")
                min_p = self.format_price(raw.min_price)
                max_p = self.format_price(raw.max_price)
                emoji = self.get_confidence_emoji(raw.confidence)
                lines.append(f"└ {emoji} {min_p} \\- {max_p}")
                lines.append("")

        # Graded prices header
        lines.append("*Graded Values:*")

        # PSA 10
        if "PSA 10" in estimates:
            psa10 = estimates["PSA 10"]
            if psa10.min_price is not None:
                min_p = self.format_price(psa10.min_price)
                max_p = self.format_price(psa10.max_price)
                emoji = self.get_confidence_emoji(psa10.confidence)
                lines.append(f"🏆 PSA 10: {emoji} *{min_p} \\- {max_p}*")
            else:
                lines.append(f"🏆 PSA 10: 🔴 Unavailable")

        # PSA 9
        if "PSA 9" in estimates:
            psa9 = estimates["PSA 9"]
            if psa9.min_price is not None:
                min_p = self.format_price(psa9.min_price)
                max_p = self.format_price(psa9.max_price)
                emoji = self.get_confidence_emoji(psa9.confidence)
                lines.append(f"🥇 PSA 9: {emoji} {min_p} \\- {max_p}")
            else:
                lines.append(f"🥇 PSA 9: 🔴 Unavailable")

        # PSA 8
        if "PSA 8" in estimates:
            psa8 = estimates["PSA 8"]
            if psa8.min_price is not None:
                min_p = self.format_price(psa8.min_price)
                max_p = self.format_price(psa8.max_price)
                emoji = self.get_confidence_emoji(psa8.confidence)
                lines.append(f"🥈 PSA 8: {emoji} {min_p} \\- {max_p}")
            else:
                lines.append(f"🥈 PSA 8: 🔴 Unavailable")

        # PSA 7 if available
        if "PSA 7" in estimates:
            psa7 = estimates["PSA 7"]
            if psa7.min_price is not None:
                min_p = self.format_price(psa7.min_price)
                max_p = self.format_price(psa7.max_price)
                emoji = self.get_confidence_emoji(psa7.confidence)
                lines.append(f"🥉 PSA 7: {emoji} {min_p} \\- {max_p}")

        lines.append("")

        # Confidence legend
        lines.append("_Confidence: 🟢High 🟡Medium 🟠Low_")

        # Verification note
        if primary_source != "verified":
            lines.append("")
            lines.append("🔍 *Always verify on eBay Sold\\!*")

            # Add search suggestion if available
            any_estimate = next((e for e in estimates.values() if e and e.search_suggestion), None)
            if any_estimate and any_estimate.search_suggestion:
                search = self.escape_md(any_estimate.search_suggestion)
                lines.append(f"Search: `{search}`")

        # Last verified date if available
        verified_estimate = next(
            (e for e in estimates.values() if e and e.source == "verified" and e.last_verified),
            None
        )
        if verified_estimate:
            lines.append("")
            last_ver = self.escape_md(verified_estimate.last_verified)
            lines.append(f"📅 Last verified: {last_ver}")

        return "\n".join(lines)

    def format_unavailable_section(self, card_info: dict = None) -> str:
        """
        Format response when prices are completely unavailable.

        Args:
            card_info: Optional card info for search suggestions
        """
        lines = [
            "💰 *PRICE ESTIMATE UNAVAILABLE*",
            "",
            "⚠️ We don't have enough reliable data for this card\\.",
            "",
            "🔍 *To find the actual price:*",
            "1\\. Search eBay Sold listings",
            "2\\. Check PSA Auction Prices Realized",
            "3\\. Look on CardMarket \\(Europe\\)",
            "",
        ]

        if card_info:
            player = card_info.get("player_character", "")
            set_name = card_info.get("set_name", "")
            year = card_info.get("year", "")
            search = f"{year} {set_name} {player} PSA sold".strip()
            search = self.escape_md(search)
            lines.append(f"📊 Suggested search: `{search}`")

        return "\n".join(lines)

    def format_admin_price_entry(self, card_id: str, card_data: dict) -> str:
        """Format price entry for admin view."""
        lines = [
            f"*Card ID:* `{self.escape_md(card_id)}`",
            f"*Name:* {self.escape_md(card_data.get('name', 'N/A'))}",
            f"*Year:* {card_data.get('year', 'N/A')}",
            f"*Set:* {self.escape_md(card_data.get('set', 'N/A'))}",
            f"*Category:* {self.escape_md(card_data.get('category', 'N/A'))}",
            "",
            "*Verified Prices:*"
        ]

        for grade, price in card_data.get("prices", {}).items():
            min_p = price.get("min", 0)
            max_p = price.get("max", 0)
            last_ver = price.get("last_verified", "N/A")
            lines.append(
                f"• {self.escape_md(grade)}: ${min_p} \\- ${max_p} \\(verified: {self.escape_md(last_ver)}\\)"
            )

        return "\n".join(lines)
