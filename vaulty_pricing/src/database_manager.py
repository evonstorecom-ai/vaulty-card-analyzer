"""
Vaulty Pricing - Database Manager
Handles loading, saving, and querying the verified prices database
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from difflib import SequenceMatcher

# Get the database directory path
DB_DIR = Path(__file__).parent.parent / "database"


class DatabaseManager:
    """Manages the verified prices and player tiers databases."""

    def __init__(self):
        self.verified_prices = {}
        self.player_tiers = {}
        self._load_databases()

    def _load_databases(self) -> None:
        """Load all database files."""
        # Load verified prices
        prices_path = DB_DIR / "verified_prices.json"
        if prices_path.exists():
            with open(prices_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.verified_prices = data.get("cards", {})

        # Load player tiers
        tiers_path = DB_DIR / "player_tiers.json"
        if tiers_path.exists():
            with open(tiers_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Remove metadata, keep only sport categories
                self.player_tiers = {k: v for k, v in data.items() if not k.startswith("_")}

    def save_verified_prices(self) -> None:
        """Save the verified prices database."""
        prices_path = DB_DIR / "verified_prices.json"
        output = {
            "_metadata": {
                "version": "1.0.0",
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "description": "Verified card prices from eBay Sold and PSA APR"
            },
            "cards": self.verified_prices
        }
        with open(prices_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

    def normalize_card_id(self, card_info: dict) -> str:
        """
        Generate a normalized card ID from card information.

        Args:
            card_info: Dictionary with card details

        Returns:
            Normalized string ID for database lookup
        """
        parts = []

        # Year
        year = card_info.get("year", "")
        if year:
            parts.append(str(year))

        # Set name (normalized)
        set_name = card_info.get("set_name", "") or card_info.get("set", "")
        if set_name:
            set_normalized = re.sub(r'[^a-z0-9]', '_', set_name.lower())
            set_normalized = re.sub(r'_+', '_', set_normalized).strip('_')
            parts.append(set_normalized)

        # Player/character name
        player = card_info.get("player_character", "") or card_info.get("player", "")
        if player:
            player_normalized = re.sub(r'[^a-z0-9]', '_', player.lower())
            player_normalized = re.sub(r'_+', '_', player_normalized).strip('_')
            parts.append(player_normalized)

        # Card number
        card_num = card_info.get("card_number", "")
        if card_num:
            num_normalized = re.sub(r'[^a-z0-9]', '', str(card_num).lower())
            if num_normalized:
                parts.append(num_normalized)

        return "_".join(parts)

    def find_card(self, card_info: dict) -> Optional[dict]:
        """
        Find a card in the verified prices database.

        Args:
            card_info: Dictionary with card details from AI analysis

        Returns:
            Card data if found, None otherwise
        """
        # Try exact match first
        card_id = self.normalize_card_id(card_info)
        if card_id in self.verified_prices:
            return self.verified_prices[card_id]

        # Try fuzzy matching
        best_match = None
        best_score = 0.0

        player = card_info.get("player_character", "") or card_info.get("player", "")
        year = str(card_info.get("year", ""))
        set_name = card_info.get("set_name", "") or card_info.get("set", "")

        for db_id, db_card in self.verified_prices.items():
            score = 0.0

            # Check year match
            if year and str(db_card.get("year", "")) == year:
                score += 0.3

            # Check player match
            db_players = db_card.get("players", [])
            if player:
                for db_player in db_players:
                    similarity = SequenceMatcher(None, player.lower(), db_player.lower()).ratio()
                    if similarity > 0.8:
                        score += 0.4 * similarity

            # Check set match
            db_set = db_card.get("set", "")
            if set_name and db_set:
                set_similarity = SequenceMatcher(None, set_name.lower(), db_set.lower()).ratio()
                if set_similarity > 0.7:
                    score += 0.3 * set_similarity

            if score > best_score and score >= 0.7:
                best_score = score
                best_match = db_card

        return best_match

    def get_player_tier(self, player_name: str, category: str = None) -> str:
        """
        Get the tier classification for a player.

        Args:
            player_name: Name of the player/character
            category: Sport/category (basketball, football, etc.)

        Returns:
            Tier string (GOAT, legend, superstar, star, starter, role_player, bust, unknown)
        """
        player_lower = player_name.lower()

        # If category is specified, search only that category
        categories_to_search = [category.lower()] if category else self.player_tiers.keys()

        for cat in categories_to_search:
            if cat not in self.player_tiers:
                continue

            for tier, players in self.player_tiers[cat].items():
                for p in players:
                    if player_lower in p.lower() or p.lower() in player_lower:
                        return tier

        return "unknown"

    def add_verified_price(
        self,
        card_id: str,
        name: str,
        year: int,
        set_name: str,
        card_number: str,
        players: list,
        category: str,
        card_type: str,
        grade: str,
        price_min: float,
        price_max: float,
        source: str = "eBay Sold"
    ) -> None:
        """
        Add or update a verified price in the database.

        Args:
            card_id: Unique identifier for the card
            name: Full card name
            year: Year of the card
            set_name: Card set name
            card_number: Card number
            players: List of player names
            category: Sport/category
            card_type: Card type (base, rookie, auto, etc.)
            grade: Grade (PSA 10, PSA 9, etc.)
            price_min: Minimum price
            price_max: Maximum price
            source: Price source
        """
        if card_id not in self.verified_prices:
            self.verified_prices[card_id] = {
                "name": name,
                "year": year,
                "set": set_name,
                "card_number": card_number,
                "players": players,
                "category": category,
                "type": card_type,
                "is_rookie": "rookie" in card_type.lower(),
                "prices": {},
                "population": {},
                "confidence": 0.85,
                "source": source,
                "notes": ""
            }

        # Update/add the price for this grade
        avg_price = (price_min + price_max) / 2
        self.verified_prices[card_id]["prices"][grade] = {
            "min": price_min,
            "max": price_max,
            "avg": avg_price,
            "last_verified": datetime.now().strftime("%Y-%m")
        }

        # Save to file
        self.save_verified_prices()

    def update_price(
        self,
        card_id: str,
        grade: str,
        price_min: float,
        price_max: float
    ) -> bool:
        """
        Update an existing price entry.

        Args:
            card_id: Card identifier
            grade: Grade to update
            price_min: New minimum price
            price_max: New maximum price

        Returns:
            True if updated, False if card not found
        """
        if card_id not in self.verified_prices:
            return False

        avg_price = (price_min + price_max) / 2
        self.verified_prices[card_id]["prices"][grade] = {
            "min": price_min,
            "max": price_max,
            "avg": avg_price,
            "last_verified": datetime.now().strftime("%Y-%m")
        }

        self.save_verified_prices()
        return True

    def get_stale_prices(self, days: int = 90) -> list:
        """
        Get list of cards with prices older than specified days.

        Args:
            days: Number of days after which price is considered stale

        Returns:
            List of (card_id, card_name, grade, last_verified) tuples
        """
        stale = []
        cutoff_date = datetime.now()

        for card_id, card in self.verified_prices.items():
            for grade, price_data in card.get("prices", {}).items():
                last_verified = price_data.get("last_verified", "")
                if last_verified:
                    try:
                        verified_date = datetime.strptime(last_verified, "%Y-%m")
                        diff_days = (cutoff_date - verified_date).days
                        if diff_days > days:
                            stale.append((
                                card_id,
                                card.get("name", card_id),
                                grade,
                                last_verified
                            ))
                    except ValueError:
                        stale.append((card_id, card.get("name", card_id), grade, "unknown"))

        return stale

    def search_cards(self, query: str, limit: int = 10) -> list:
        """
        Search for cards in the database.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching cards
        """
        results = []
        query_lower = query.lower()

        for card_id, card in self.verified_prices.items():
            score = 0

            # Check card name
            if query_lower in card.get("name", "").lower():
                score += 2

            # Check players
            for player in card.get("players", []):
                if query_lower in player.lower():
                    score += 1

            # Check set
            if query_lower in card.get("set", "").lower():
                score += 0.5

            if score > 0:
                results.append((score, card_id, card))

        # Sort by score and return top matches
        results.sort(reverse=True, key=lambda x: x[0])
        return [(card_id, card) for _, card_id, card in results[:limit]]

    def export_database(self) -> dict:
        """Export the full database for backup."""
        return {
            "verified_prices": self.verified_prices,
            "player_tiers": self.player_tiers,
            "exported_at": datetime.now().isoformat()
        }

    def get_stats(self) -> dict:
        """Get database statistics."""
        total_cards = len(self.verified_prices)
        total_prices = sum(
            len(card.get("prices", {}))
            for card in self.verified_prices.values()
        )

        categories = {}
        for card in self.verified_prices.values():
            cat = card.get("category", "Unknown")
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_cards": total_cards,
            "total_price_entries": total_prices,
            "categories": categories,
            "last_updated": datetime.now().isoformat()
        }
