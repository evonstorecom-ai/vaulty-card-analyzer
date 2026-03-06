#!/usr/bin/env python3
"""
External Search Module for Vaulty Card Analyzer

Multi-source card identification using:
1. Google Lens (via SerpAPI) - Reverse image search
2. Scryfall API - Magic: The Gathering cards
3. Pokemon TCG API - Pokemon cards
4. eBay API - All trading cards with sold prices
5. Web scraping fallback

This module enables much better card recognition by cross-referencing
multiple external sources.
"""

import aiohttp
import asyncio
import base64
import json
import os
import re
import logging
from typing import Optional
from urllib.parse import quote_plus, urlencode

logger = logging.getLogger(__name__)

# API Keys (from environment)
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID", "")


class ExternalCardSearch:
    """Multi-source card identification system."""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache = {}

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    # =========================================================================
    # GOOGLE LENS / SERPAPI - Reverse Image Search
    # =========================================================================

    async def google_lens_search(self, image_bytes: bytes) -> dict:
        """
        Search Google Lens using SerpAPI for reverse image search.
        This is the most powerful method for identifying unknown cards.
        """
        if not SERPAPI_KEY:
            logger.warning("SERPAPI_KEY not configured, skipping Google Lens")
            return {"success": False, "error": "SERPAPI_KEY not configured"}

        try:
            session = await self._get_session()

            # Convert image to base64 for upload
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')

            # SerpAPI Google Lens endpoint
            params = {
                "engine": "google_lens",
                "api_key": SERPAPI_KEY,
            }

            # First, upload the image and get results
            url = "https://serpapi.com/search"

            # For Google Lens, we need to use URL or upload
            # Using the data_uri approach
            data_uri = f"data:image/jpeg;base64,{image_b64}"

            params["url"] = data_uri

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_google_lens_results(data)
                else:
                    error_text = await response.text()
                    logger.error(f"Google Lens API error: {response.status} - {error_text}")
                    return {"success": False, "error": f"API error: {response.status}"}

        except Exception as e:
            logger.error(f"Google Lens search error: {e}")
            return {"success": False, "error": str(e)}

    def _parse_google_lens_results(self, data: dict) -> dict:
        """Parse Google Lens API response to extract card information."""
        results = {
            "success": True,
            "source": "google_lens",
            "matches": [],
            "visual_matches": [],
            "knowledge_graph": None,
            "detected_text": []
        }

        # Extract visual matches (similar images)
        if "visual_matches" in data:
            for match in data["visual_matches"][:10]:
                results["visual_matches"].append({
                    "title": match.get("title", ""),
                    "link": match.get("link", ""),
                    "source": match.get("source", ""),
                    "thumbnail": match.get("thumbnail", ""),
                    "price": self._extract_price_from_text(match.get("title", ""))
                })

        # Extract knowledge graph (card identification)
        if "knowledge_graph" in data:
            kg = data["knowledge_graph"]
            results["knowledge_graph"] = {
                "title": kg.get("title", ""),
                "subtitle": kg.get("subtitle", ""),
                "description": kg.get("description", ""),
                "images": kg.get("images", [])
            }

        # Extract detected text from the image
        if "text_results" in data:
            results["detected_text"] = [
                t.get("text", "") for t in data.get("text_results", [])
            ]

        # Try to identify the card from results
        card_info = self._identify_card_from_lens(results)
        results["identified_card"] = card_info

        return results

    def _identify_card_from_lens(self, lens_results: dict) -> dict:
        """Attempt to identify the card from Google Lens results."""
        card_info = {
            "name": None,
            "game": None,
            "set": None,
            "number": None,
            "confidence": 0
        }

        # Analyze visual matches
        for match in lens_results.get("visual_matches", []):
            title = match.get("title", "").lower()
            source = match.get("source", "").lower()

            # Check for card marketplace sources
            if any(site in source for site in ["ebay", "tcgplayer", "cardmarket", "pokellector", "psa"]):
                parsed = self._parse_card_title(match.get("title", ""))
                if parsed["confidence"] > card_info["confidence"]:
                    card_info = parsed

        # Check knowledge graph
        if lens_results.get("knowledge_graph"):
            kg = lens_results["knowledge_graph"]
            parsed = self._parse_card_title(kg.get("title", ""))
            if parsed["confidence"] > card_info["confidence"]:
                card_info = parsed

        return card_info

    def _parse_card_title(self, title: str) -> dict:
        """Parse a card title from search results to extract card info."""
        result = {
            "name": None,
            "game": None,
            "set": None,
            "number": None,
            "year": None,
            "player": None,
            "parallel": None,
            "confidence": 0
        }

        if not title:
            return result

        title_lower = title.lower()

        # Detect game type
        if any(word in title_lower for word in ["pokemon", "pikachu", "charizard", "pokémon"]):
            result["game"] = "Pokemon"
            result["confidence"] += 20
        elif any(word in title_lower for word in ["magic", "mtg", "gathering", "mana"]):
            result["game"] = "MTG"
            result["confidence"] += 20
        elif any(word in title_lower for word in ["yugioh", "yu-gi-oh", "duel monster"]):
            result["game"] = "Yu-Gi-Oh"
            result["confidence"] += 20
        elif any(word in title_lower for word in ["topps", "panini", "prizm", "donruss", "upper deck", "fleer", "bowman"]):
            result["game"] = "Sports"
            result["confidence"] += 20
        elif any(word in title_lower for word in ["nba", "basketball", "nfl", "football", "mlb", "baseball", "nhl", "hockey"]):
            result["game"] = "Sports"
            result["confidence"] += 15

        # Extract card number patterns
        card_num_match = re.search(r'#?\s*(\d{1,4})\s*[/\\]\s*(\d{1,4})', title)
        if card_num_match:
            result["number"] = f"{card_num_match.group(1)}/{card_num_match.group(2)}"
            result["confidence"] += 15
        else:
            card_num_match = re.search(r'#\s*(\d{1,4})', title)
            if card_num_match:
                result["number"] = card_num_match.group(1)
                result["confidence"] += 10

        # Extract year
        year_match = re.search(r'(19\d{2}|20\d{2})', title)
        if year_match:
            result["year"] = year_match.group(1)
            result["confidence"] += 10

        # Extract set names (common patterns)
        set_patterns = [
            r'(prizm|select|mosaic|optic|donruss|topps chrome|bowman|fleer|upper deck)',
            r'(base set|jungle|fossil|team rocket|gym heroes|neo|expedition)',
            r'(scarlet\s*&?\s*violet|sword\s*&?\s*shield|sun\s*&?\s*moon)',
        ]
        for pattern in set_patterns:
            set_match = re.search(pattern, title_lower)
            if set_match:
                result["set"] = set_match.group(1).title()
                result["confidence"] += 15
                break

        # Extract parallel types
        parallel_patterns = [
            r'(holo|holofoil|holographic|reverse holo)',
            r'(refractor|prizm|mosaic|shimmer)',
            r'(gold|silver|blue|red|green|orange|purple)\s*(parallel|wave|ice)?',
            r'(/\d{1,3})\s*(numbered)?',
            r'(1/1|one of one)',
            r'(psa\s*\d{1,2}|bgs\s*\d)',
        ]
        for pattern in parallel_patterns:
            parallel_match = re.search(pattern, title_lower)
            if parallel_match:
                result["parallel"] = parallel_match.group(1)
                result["confidence"] += 10
                break

        # Clean and set the name (usually first part before numbers/special chars)
        name_part = re.split(r'[#\d/\-]', title)[0].strip()
        # Remove common prefixes/suffixes
        name_part = re.sub(r'(psa|bgs|cgc|sgc|\d{4})', '', name_part, flags=re.IGNORECASE).strip()
        if len(name_part) > 3:
            result["name"] = name_part
            result["confidence"] += 20

        return result

    def _extract_price_from_text(self, text: str) -> Optional[float]:
        """Extract price from text."""
        if not text:
            return None

        # Match various price formats
        patterns = [
            r'\$\s*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*(?:USD|EUR|€|\$)',
            r'€\s*([\d,]+\.?\d*)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    price_str = match.group(1).replace(',', '')
                    return float(price_str)
                except ValueError:
                    continue
        return None

    # =========================================================================
    # SCRYFALL API - Magic: The Gathering
    # =========================================================================

    async def search_scryfall(self, query: str = None, set_code: str = None,
                               collector_number: str = None) -> dict:
        """Search Scryfall for MTG cards."""
        try:
            session = await self._get_session()

            if set_code and collector_number:
                # Direct lookup
                url = f"https://api.scryfall.com/cards/{set_code}/{collector_number}"
                async with session.get(url) as response:
                    if response.status == 200:
                        card = await response.json()
                        return self._format_scryfall_result(card)

            if query:
                # Fuzzy search
                url = f"https://api.scryfall.com/cards/named"
                params = {"fuzzy": query}
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        card = await response.json()
                        return self._format_scryfall_result(card)

                # If fuzzy fails, try search
                url = "https://api.scryfall.com/cards/search"
                params = {"q": query, "unique": "prints"}
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("data"):
                            return self._format_scryfall_result(data["data"][0])

            return {"success": False, "error": "Card not found"}

        except Exception as e:
            logger.error(f"Scryfall search error: {e}")
            return {"success": False, "error": str(e)}

    def _format_scryfall_result(self, card: dict) -> dict:
        """Format Scryfall card data."""
        prices = card.get("prices", {})
        return {
            "success": True,
            "source": "scryfall",
            "game": "MTG",
            "name": card.get("name"),
            "set": card.get("set_name"),
            "set_code": card.get("set"),
            "number": card.get("collector_number"),
            "rarity": card.get("rarity"),
            "image_url": card.get("image_uris", {}).get("normal"),
            "prices": {
                "usd": float(prices.get("usd") or 0),
                "usd_foil": float(prices.get("usd_foil") or 0),
                "eur": float(prices.get("eur") or 0),
            },
            "scryfall_uri": card.get("scryfall_uri"),
            "tcgplayer_id": card.get("tcgplayer_id"),
        }

    # =========================================================================
    # POKEMON TCG API
    # =========================================================================

    async def search_pokemon_tcg(self, query: str = None, set_id: str = None,
                                  number: str = None) -> dict:
        """Search Pokemon TCG API for cards."""
        try:
            session = await self._get_session()

            url = "https://api.pokemontcg.io/v2/cards"
            headers = {}

            # API key is optional but recommended
            pokemon_api_key = os.environ.get("POKEMON_TCG_API_KEY", "")
            if pokemon_api_key:
                headers["X-Api-Key"] = pokemon_api_key

            # Build query
            if set_id and number:
                params = {"q": f"set.id:{set_id} number:{number}"}
            elif query:
                # Search by name
                params = {"q": f"name:{query}*", "pageSize": 10}
            else:
                return {"success": False, "error": "No search criteria provided"}

            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    cards = data.get("data", [])
                    if cards:
                        return self._format_pokemon_result(cards[0])

            return {"success": False, "error": "Card not found"}

        except Exception as e:
            logger.error(f"Pokemon TCG search error: {e}")
            return {"success": False, "error": str(e)}

    def _format_pokemon_result(self, card: dict) -> dict:
        """Format Pokemon TCG card data."""
        tcgplayer = card.get("tcgplayer", {})
        prices = tcgplayer.get("prices", {})

        # Get the best price data available
        price_data = {}
        for variant in ["holofoil", "reverseHolofoil", "normal", "1stEditionHolofoil"]:
            if variant in prices:
                price_data = prices[variant]
                break

        return {
            "success": True,
            "source": "pokemon_tcg",
            "game": "Pokemon",
            "name": card.get("name"),
            "set": card.get("set", {}).get("name"),
            "set_id": card.get("set", {}).get("id"),
            "number": card.get("number"),
            "rarity": card.get("rarity"),
            "image_url": card.get("images", {}).get("large"),
            "prices": {
                "low": price_data.get("low", 0),
                "mid": price_data.get("mid", 0),
                "high": price_data.get("high", 0),
                "market": price_data.get("market", 0),
            },
            "tcgplayer_url": tcgplayer.get("url"),
            "cardmarket_url": card.get("cardmarket", {}).get("url"),
        }

    # =========================================================================
    # EBAY SEARCH (via Web Scraping or API)
    # =========================================================================

    async def search_ebay_sold(self, query: str, game: str = None) -> dict:
        """
        Search eBay sold listings for price references.
        Uses web scraping as eBay API requires business registration.
        """
        try:
            session = await self._get_session()

            # Build search URL
            search_query = quote_plus(query)
            url = f"https://www.ebay.com/sch/i.html?_nkw={search_query}&LH_Complete=1&LH_Sold=1&_sop=13"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_ebay_results(html, query)

            return {"success": False, "error": "eBay request failed"}

        except Exception as e:
            logger.error(f"eBay search error: {e}")
            return {"success": False, "error": str(e)}

    def _parse_ebay_results(self, html: str, query: str) -> dict:
        """Parse eBay search results HTML."""
        results = {
            "success": True,
            "source": "ebay_sold",
            "query": query,
            "listings": [],
            "price_summary": {
                "min": None,
                "max": None,
                "avg": None,
                "count": 0
            }
        }

        # Extract prices using regex (basic parsing)
        price_pattern = r'\$(\d{1,6}(?:,\d{3})*(?:\.\d{2})?)'
        prices = []

        # Find all prices
        for match in re.finditer(price_pattern, html):
            try:
                price = float(match.group(1).replace(',', ''))
                if 0.01 < price < 100000:  # Reasonable price range
                    prices.append(price)
            except ValueError:
                continue

        if prices:
            # Take middle portion to avoid outliers
            prices.sort()
            if len(prices) > 4:
                prices = prices[1:-1]  # Remove highest and lowest

            results["price_summary"] = {
                "min": min(prices),
                "max": max(prices),
                "avg": sum(prices) / len(prices),
                "count": len(prices)
            }

        return results

    # =========================================================================
    # UNIFIED SEARCH - Combine all sources
    # =========================================================================

    async def identify_card(self, image_bytes: bytes,
                            claude_hints: dict = None) -> dict:
        """
        Main method: Identify a card using multiple sources.

        Args:
            image_bytes: Raw image data
            claude_hints: Optional hints from Claude Vision analysis

        Returns:
            Comprehensive card identification with prices
        """
        results = {
            "success": False,
            "sources_checked": [],
            "best_match": None,
            "all_matches": [],
            "prices": {},
            "confidence": 0,
            "search_urls": {}
        }

        # 1. Try Google Lens first (most powerful for unknown cards)
        lens_result = await self.google_lens_search(image_bytes)
        results["sources_checked"].append("google_lens")

        if lens_result.get("success"):
            results["google_lens"] = lens_result
            identified = lens_result.get("identified_card", {})

            if identified.get("confidence", 0) > 30:
                results["best_match"] = identified
                results["confidence"] = identified["confidence"]

                # Get game-specific details
                game = identified.get("game")
                name = identified.get("name")

                if game == "MTG" and name:
                    mtg_result = await self.search_scryfall(query=name)
                    results["sources_checked"].append("scryfall")
                    if mtg_result.get("success"):
                        results["all_matches"].append(mtg_result)
                        results["prices"]["scryfall"] = mtg_result.get("prices", {})
                        results["confidence"] += 20

                elif game == "Pokemon" and name:
                    pokemon_result = await self.search_pokemon_tcg(query=name)
                    results["sources_checked"].append("pokemon_tcg")
                    if pokemon_result.get("success"):
                        results["all_matches"].append(pokemon_result)
                        results["prices"]["pokemon_tcg"] = pokemon_result.get("prices", {})
                        results["confidence"] += 20

        # 2. If we have Claude hints, use them for additional searches
        if claude_hints:
            game = claude_hints.get("game", "").lower()
            card_name = claude_hints.get("card_name", "")
            set_name = claude_hints.get("set_name", "")

            if "magic" in game or "mtg" in game:
                if card_name and "scryfall" not in results["sources_checked"]:
                    mtg_result = await self.search_scryfall(query=card_name)
                    results["sources_checked"].append("scryfall")
                    if mtg_result.get("success"):
                        results["all_matches"].append(mtg_result)
                        if not results["best_match"]:
                            results["best_match"] = {
                                "name": mtg_result["name"],
                                "game": "MTG",
                                "set": mtg_result["set"],
                                "confidence": 70
                            }
                        results["prices"]["scryfall"] = mtg_result.get("prices", {})

            elif "pokemon" in game or "pokémon" in game:
                if card_name and "pokemon_tcg" not in results["sources_checked"]:
                    pokemon_result = await self.search_pokemon_tcg(query=card_name)
                    results["sources_checked"].append("pokemon_tcg")
                    if pokemon_result.get("success"):
                        results["all_matches"].append(pokemon_result)
                        if not results["best_match"]:
                            results["best_match"] = {
                                "name": pokemon_result["name"],
                                "game": "Pokemon",
                                "set": pokemon_result["set"],
                                "confidence": 70
                            }
                        results["prices"]["pokemon_tcg"] = pokemon_result.get("prices", {})

            # Always try eBay for price validation
            if card_name:
                search_query = f"{card_name} {set_name}".strip()
                ebay_result = await self.search_ebay_sold(search_query, game)
                results["sources_checked"].append("ebay_sold")
                if ebay_result.get("success"):
                    results["prices"]["ebay_sold"] = ebay_result.get("price_summary", {})

        # Generate search URLs for manual verification
        if results.get("best_match"):
            match = results["best_match"]
            name = match.get("name", "")
            game = match.get("game", "")
            set_name = match.get("set", "")

            query = quote_plus(f"{name} {set_name}".strip())
            results["search_urls"] = {
                "ebay_sold": f"https://www.ebay.com/sch/i.html?_nkw={query}&LH_Complete=1&LH_Sold=1",
                "tcgplayer": f"https://www.tcgplayer.com/search/all/product?q={query}",
                "cardmarket": f"https://www.cardmarket.com/en/Search?searchString={query}",
            }

        results["success"] = results["confidence"] > 30 or len(results["all_matches"]) > 0
        return results

    async def get_prices_for_card(self, card_name: str, game: str,
                                   set_name: str = None) -> dict:
        """Get current market prices for a specific card."""
        prices = {}

        if game.lower() in ["mtg", "magic"]:
            result = await self.search_scryfall(query=card_name)
            if result.get("success"):
                prices["scryfall"] = result.get("prices", {})

        elif game.lower() == "pokemon":
            result = await self.search_pokemon_tcg(query=card_name)
            if result.get("success"):
                prices["pokemon_tcg"] = result.get("prices", {})

        # Always check eBay sold
        search_query = f"{card_name} {set_name or ''} {game}".strip()
        ebay_result = await self.search_ebay_sold(search_query)
        if ebay_result.get("success"):
            prices["ebay_sold"] = ebay_result.get("price_summary", {})

        return prices


# Singleton instance
_search_instance: Optional[ExternalCardSearch] = None


def get_search_instance() -> ExternalCardSearch:
    """Get or create the search instance."""
    global _search_instance
    if _search_instance is None:
        _search_instance = ExternalCardSearch()
    return _search_instance


async def identify_card_external(image_bytes: bytes,
                                  claude_hints: dict = None) -> dict:
    """Convenience function for card identification."""
    searcher = get_search_instance()
    return await searcher.identify_card(image_bytes, claude_hints)
