"""
Vaulty Pricing - Price Estimator
Main algorithm for estimating card prices with confidence levels
"""

import re
from typing import Optional
from dataclasses import dataclass

from ..config import (
    GRADE_MULTIPLIERS,
    PLAYER_TIERS,
    RARITY_MULTIPLIERS,
    SET_MULTIPLIERS,
    CATEGORY_BASE_PRICES,
    POPULATION_MULTIPLIERS,
    MIN_CONFIDENCE_TO_DISPLAY,
)
from .database_manager import DatabaseManager


@dataclass
class PriceEstimate:
    """Data class for price estimation results."""
    min_price: Optional[float]
    max_price: Optional[float]
    avg_price: Optional[float]
    confidence: float
    source: str  # "verified", "algorithm", "unavailable"
    grade: str
    currency: str = "USD"
    last_verified: Optional[str] = None
    notes: Optional[str] = None
    search_suggestion: Optional[str] = None


class PriceEstimator:
    """
    Estimates card prices using verified database and algorithmic calculations.
    Prioritizes accuracy and transparency in confidence levels.
    """

    def __init__(self):
        self.db = DatabaseManager()

    def estimate_price(self, card_info: dict, grade: str = "RAW") -> PriceEstimate:
        """
        Estimate the price of a card.

        Priority:
        1. Verified database lookup
        2. Algorithmic calculation
        3. Return unavailable if confidence too low

        Args:
            card_info: Dictionary with card identification from AI analysis
            grade: Grade to estimate (PSA 10, PSA 9, RAW, etc.)

        Returns:
            PriceEstimate with price range and confidence level
        """
        # Normalize grade
        grade = self._normalize_grade(grade)

        # Step 1: Try verified database
        verified_result = self._lookup_verified_price(card_info, grade)
        if verified_result:
            return verified_result

        # Step 2: Calculate algorithmically
        calculated_result = self._calculate_price(card_info, grade)

        # Step 3: Check if confidence is high enough
        if calculated_result.confidence < MIN_CONFIDENCE_TO_DISPLAY:
            return self._unavailable_result(card_info, grade)

        return calculated_result

    def estimate_all_grades(self, card_info: dict) -> dict:
        """
        Estimate prices for all common grades.

        Args:
            card_info: Card identification dictionary

        Returns:
            Dictionary mapping grade to PriceEstimate
        """
        grades = ["PSA 10", "PSA 9", "PSA 8", "PSA 7", "RAW"]
        return {grade: self.estimate_price(card_info, grade) for grade in grades}

    def _normalize_grade(self, grade: str) -> str:
        """Normalize grade string to standard format."""
        grade = grade.upper().strip()

        # Handle common variations
        grade_map = {
            "10": "PSA 10",
            "9": "PSA 9",
            "8": "PSA 8",
            "7": "PSA 7",
            "6": "PSA 6",
            "GEM MINT": "PSA 10",
            "GEM MT": "PSA 10",
            "MINT": "PSA 9",
            "NM-MT": "PSA 8",
            "NM": "PSA 7",
            "UNGRADED": "RAW",
        }

        return grade_map.get(grade, grade)

    def _lookup_verified_price(self, card_info: dict, grade: str) -> Optional[PriceEstimate]:
        """Look up price in verified database."""
        card_data = self.db.find_card(card_info)

        if not card_data:
            return None

        prices = card_data.get("prices", {})
        if grade not in prices:
            return None

        price_data = prices[grade]
        confidence = card_data.get("confidence", 0.85)

        return PriceEstimate(
            min_price=price_data.get("min"),
            max_price=price_data.get("max"),
            avg_price=price_data.get("avg"),
            confidence=confidence,
            source="verified",
            grade=grade,
            last_verified=price_data.get("last_verified"),
            notes=card_data.get("notes")
        )

    def _calculate_price(self, card_info: dict, grade: str) -> PriceEstimate:
        """
        Calculate price using weighted factors algorithm.
        This is used when card is not in verified database.
        """
        # Get base price for category
        category = card_info.get("sport_category", "default")
        base_price = CATEGORY_BASE_PRICES.get(category, CATEGORY_BASE_PRICES["default"])

        # Calculate multipliers
        grade_mult = self._get_grade_multiplier(grade)
        player_mult = self._get_player_multiplier(card_info)
        rarity_mult = self._get_rarity_multiplier(card_info)
        set_mult = self._get_set_multiplier(card_info)
        year_mult = self._get_year_multiplier(card_info)

        # Calculate base estimated price
        calculated_price = (
            base_price
            * grade_mult
            * player_mult
            * rarity_mult
            * set_mult
            * year_mult
        )

        # Determine confidence based on how much info we have
        confidence = self._calculate_confidence(card_info, player_mult, rarity_mult)

        # Apply margin of error (±30% for algorithmic estimates)
        margin = 0.30
        min_price = round(calculated_price * (1 - margin), 2)
        max_price = round(calculated_price * (1 + margin), 2)
        avg_price = round(calculated_price, 2)

        # Generate search suggestion
        player = card_info.get("player_character", "card")
        set_name = card_info.get("set_name", "")
        year = card_info.get("year", "")
        search_query = f"{year} {set_name} {player} {grade} sold".strip()

        return PriceEstimate(
            min_price=min_price,
            max_price=max_price,
            avg_price=avg_price,
            confidence=confidence,
            source="algorithm",
            grade=grade,
            notes="Estimated algorithmically - verify on eBay Sold",
            search_suggestion=search_query
        )

    def _get_grade_multiplier(self, grade: str) -> float:
        """Get the multiplier for a grade."""
        return GRADE_MULTIPLIERS.get(grade, 1.0)

    def _get_player_multiplier(self, card_info: dict) -> float:
        """Get multiplier based on player tier."""
        player = card_info.get("player_character", "")
        category = card_info.get("sport_category", "")

        # Map category to player tier category
        category_map = {
            "Basketball": "basketball",
            "Football": "football",
            "Baseball": "baseball",
            "Soccer": "soccer",
            "Pokemon": "pokemon",
            "Magic: The Gathering": None,
            "Yu-Gi-Oh!": None,
        }

        tier_category = category_map.get(category)
        tier = self.db.get_player_tier(player, tier_category)

        return PLAYER_TIERS.get(tier, PLAYER_TIERS["unknown"])

    def _get_rarity_multiplier(self, card_info: dict) -> float:
        """Get multiplier based on card rarity/type."""
        multiplier = 1.0

        # Check for parallel type
        subset = card_info.get("subset_parallel", "").lower()
        if subset:
            for rarity, mult in RARITY_MULTIPLIERS.items():
                if rarity in subset:
                    multiplier = max(multiplier, mult)
                    break

        # Check for serial numbering
        serial = card_info.get("serial_numbered")
        if serial:
            serial_str = str(serial)
            if "/1" in serial_str or "1/1" in serial_str.lower():
                multiplier *= RARITY_MULTIPLIERS.get("1/1", 50.0)
            elif match := re.search(r'/(\d+)', serial_str):
                num = int(match.group(1))
                if num <= 5:
                    multiplier *= RARITY_MULTIPLIERS.get("numbered_5", 20.0)
                elif num <= 10:
                    multiplier *= RARITY_MULTIPLIERS.get("numbered_10", 12.0)
                elif num <= 25:
                    multiplier *= RARITY_MULTIPLIERS.get("numbered_25", 8.0)
                elif num <= 50:
                    multiplier *= RARITY_MULTIPLIERS.get("numbered_50", 5.0)
                elif num <= 99:
                    multiplier *= RARITY_MULTIPLIERS.get("numbered_99", 3.5)
                elif num <= 199:
                    multiplier *= RARITY_MULTIPLIERS.get("numbered_199", 2.5)
                elif num <= 299:
                    multiplier *= RARITY_MULTIPLIERS.get("numbered_299", 2.0)
                elif num <= 499:
                    multiplier *= RARITY_MULTIPLIERS.get("numbered_499", 1.5)
                else:
                    multiplier *= RARITY_MULTIPLIERS.get("numbered_999", 1.3)

        # Check for rookie
        if card_info.get("rookie_card"):
            multiplier *= RARITY_MULTIPLIERS.get("rookie", 2.0)

        # Check for auto
        if card_info.get("autograph"):
            if card_info.get("rookie_card"):
                multiplier *= RARITY_MULTIPLIERS.get("auto_rookie", 8.0) / RARITY_MULTIPLIERS.get("rookie", 2.0)
            else:
                multiplier *= RARITY_MULTIPLIERS.get("auto", 5.0)

        # Check for memorabilia
        memo = card_info.get("memorabilia")
        if memo:
            memo_lower = memo.lower()
            if "patch" in memo_lower:
                multiplier *= RARITY_MULTIPLIERS.get("patch", 4.0)
            elif "jersey" in memo_lower:
                multiplier *= RARITY_MULTIPLIERS.get("jersey", 2.5)
            elif "logoman" in memo_lower:
                multiplier *= RARITY_MULTIPLIERS.get("logoman", 30.0)

        return multiplier

    def _get_set_multiplier(self, card_info: dict) -> float:
        """Get multiplier based on card set prestige."""
        set_name = card_info.get("set_name", "")
        manufacturer = card_info.get("manufacturer", "")
        year = card_info.get("year", "")

        # Try exact set match
        full_set = f"{year} {set_name}".strip()
        if full_set in SET_MULTIPLIERS:
            return SET_MULTIPLIERS[full_set]

        # Try set name only
        if set_name in SET_MULTIPLIERS:
            return SET_MULTIPLIERS[set_name]

        # Try manufacturer + set
        mfr_set = f"{manufacturer} {set_name}".strip()
        if mfr_set in SET_MULTIPLIERS:
            return SET_MULTIPLIERS[mfr_set]

        # Check for keywords
        set_lower = set_name.lower()
        if "national treasures" in set_lower:
            return SET_MULTIPLIERS.get("Panini National Treasures", 5.0)
        elif "flawless" in set_lower:
            return SET_MULTIPLIERS.get("Panini Flawless", 6.0)
        elif "prizm" in set_lower:
            return SET_MULTIPLIERS.get("Panini Prizm", 2.0)
        elif "chrome" in set_lower:
            return SET_MULTIPLIERS.get("Topps Chrome", 2.5)
        elif "select" in set_lower:
            return SET_MULTIPLIERS.get("Panini Select", 1.8)
        elif "mosaic" in set_lower:
            return SET_MULTIPLIERS.get("Panini Mosaic", 1.5)

        return SET_MULTIPLIERS.get("default", 1.0)

    def _get_year_multiplier(self, card_info: dict) -> float:
        """Get multiplier based on year (rookie year boost, etc.)."""
        # Rookie cards already get boost from rarity multiplier
        # This handles vintage premium
        year = card_info.get("year")
        if not year:
            return 1.0

        try:
            year = int(year)
        except (ValueError, TypeError):
            return 1.0

        current_year = 2024

        # Vintage premium
        if year < 1980:
            return 2.0
        elif year < 1990:
            return 1.5
        elif year < 2000:
            return 1.2
        elif year > current_year - 2:
            # Recent cards - slight premium for hype
            return 1.1

        return 1.0

    def _calculate_confidence(self, card_info: dict, player_mult: float, rarity_mult: float) -> float:
        """
        Calculate confidence level based on available information.

        Lower confidence if:
        - Player is unknown
        - Set is unknown
        - Year is unknown
        - Card type is complex (auto/patch/numbered)
        """
        confidence = 0.70  # Base confidence for algorithmic

        # Reduce if player is unknown
        if player_mult == PLAYER_TIERS["unknown"]:
            confidence -= 0.15

        # Reduce for complex cards (harder to estimate)
        if rarity_mult > 5.0:
            confidence -= 0.10

        # Reduce if missing key info
        if not card_info.get("year"):
            confidence -= 0.10
        if not card_info.get("set_name"):
            confidence -= 0.10
        if not card_info.get("player_character"):
            confidence -= 0.15

        # Boost if we have detailed info
        if card_info.get("card_number"):
            confidence += 0.05
        if card_info.get("manufacturer"):
            confidence += 0.05

        return max(0.1, min(0.75, confidence))

    def _unavailable_result(self, card_info: dict, grade: str) -> PriceEstimate:
        """Return result when price cannot be estimated with sufficient confidence."""
        player = card_info.get("player_character", "card")
        set_name = card_info.get("set_name", "")
        year = card_info.get("year", "")
        search_query = f"{year} {set_name} {player} {grade} sold".strip()

        return PriceEstimate(
            min_price=None,
            max_price=None,
            avg_price=None,
            confidence=0.0,
            source="unavailable",
            grade=grade,
            notes="Insufficient data for reliable estimate",
            search_suggestion=search_query
        )

    def get_grade_comparison(self, card_info: dict) -> dict:
        """
        Get price comparison across different grades.
        Useful for showing value of grading.

        Returns:
            Dict with grade prices and grading ROI
        """
        estimates = self.estimate_all_grades(card_info)

        raw_price = estimates.get("RAW")
        psa10_price = estimates.get("PSA 10")

        grading_cost = 50  # Approximate PSA grading cost

        result = {"estimates": estimates}

        if raw_price and psa10_price and raw_price.avg_price and psa10_price.avg_price:
            potential_profit = psa10_price.avg_price - raw_price.avg_price - grading_cost
            result["grading_analysis"] = {
                "cost_to_grade": grading_cost,
                "potential_profit_psa10": round(potential_profit, 2),
                "worth_grading": potential_profit > 100
            }

        return result
