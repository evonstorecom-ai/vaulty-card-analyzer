"""
Price Estimator pour Vaulty Card Analyzer
Système d'estimation de prix avec facteurs pondérés et niveaux de confiance
Objectif: 80% de précision par rapport aux prix eBay Sold
"""

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
from database import db_manager

# ==================== CONFIGURATION DES FACTEURS ====================

# Multiplicateurs par grade
GRADE_MULTIPLIERS = {
    "PSA_10": 8.0,
    "PSA_9": 2.5,
    "PSA_8": 1.0,      # Base de référence
    "PSA_7": 0.6,
    "PSA_6": 0.4,
    "BGS_10": 10.0,    # Black Label
    "BGS_9.5": 3.5,
    "BGS_9": 2.0,
    "SGC_10": 4.0,
    "CGC_10": 3.0,
    "CGC_9.5": 2.5,
    "RAW": 0.3
}

# Multiplicateurs par rareté/parallèle
RARITY_MULTIPLIERS = {
    "base": 1.0,
    "holo": 2.0,
    "reverse_holo": 1.5,
    "parallel": 2.0,
    "refractor": 3.0,
    "prizm": 2.5,
    "silver_prizm": 4.0,
    "gold_prizm": 8.0,
    "auto": 5.0,
    "auto_rookie": 8.0,
    "patch": 4.0,
    "logoman": 30.0,
    "1/1": 50.0,
    "numbered_5": 20.0,
    "numbered_10": 12.0,
    "numbered_25": 8.0,
    "numbered_50": 5.0,
    "numbered_99": 3.5,
    "numbered_199": 2.5,
    "numbered_299": 2.0,
    "numbered_499": 1.5,
    "numbered_999": 1.3,
    "rookie": 2.0,
    "secret_rare": 5.0,
    "alt_art": 8.0,
    "special_art_rare": 10.0,
    "treasure_rare": 15.0,
    "manga_rare": 12.0
}

# Prix de base par catégorie (PSA 8, joueur standard)
BASE_PRICES = {
    "pokemon": 10,
    "one_piece": 8,
    "yugioh": 5,
    "magic": 15,
    "basketball": 5,
    "football": 5,
    "soccer": 5,
    "baseball": 4,
    "hockey": 3,
    "default": 5
}

# Chemin vers player_tiers.json
TIERS_PATH = Path(__file__).parent / "database" / "player_tiers.json"


@dataclass
class PriceEstimate:
    """Résultat d'une estimation de prix"""
    min_price: Optional[int]
    max_price: Optional[int]
    confidence: int  # 0-100%
    source: str  # "verified", "algorithm", "similar", "unavailable"
    grade: str
    card_name: Optional[str] = None
    last_verified: Optional[str] = None
    notes: Optional[str] = None


def load_player_tiers() -> dict:
    """Charge les tiers de joueurs depuis le fichier JSON"""
    if not TIERS_PATH.exists():
        return {"players": {}, "tiers": {}}
    with open(TIERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_player_tier(player_name: str, category: str = "") -> tuple[str, float]:
    """
    Détermine le tier d'un joueur et son multiplicateur
    Retourne: (tier_name, multiplier)
    """
    tiers_data = load_player_tiers()
    players = tiers_data.get("players", {})
    tiers = tiers_data.get("tiers", {})

    player_lower = player_name.lower().strip()

    # Chercher dans chaque catégorie
    categories_to_check = [category.lower()] if category else list(players.keys())

    for cat in categories_to_check:
        if cat not in players:
            continue
        for tier_name, player_list in players[cat].items():
            for p in player_list:
                if player_lower in p.lower() or p.lower() in player_lower:
                    multiplier = tiers.get(tier_name, {}).get("multiplier", 1.0)
                    return tier_name, multiplier

    # Joueur non trouvé
    return "unknown", tiers.get("unknown", {}).get("multiplier", 0.5)


def normalize_grade(grade: str) -> str:
    """Normalise le format du grade"""
    grade = grade.upper().strip()
    grade = grade.replace("-", "_").replace(" ", "_")

    # Corriger les formats courants
    if grade.isdigit():
        grade = f"PSA_{grade}"
    elif grade in ["GEM_MINT", "GEM_MT", "10"]:
        grade = "PSA_10"
    elif grade in ["MINT", "9"]:
        grade = "PSA_9"
    elif grade in ["NM_MT", "8"]:
        grade = "PSA_8"
    elif grade in ["UNGRADED", "NON_GRADEE"]:
        grade = "RAW"

    return grade


def get_rarity_multiplier(card_info: dict) -> float:
    """Calcule le multiplicateur de rareté basé sur les infos de la carte"""
    multiplier = 1.0

    rarity = card_info.get("rarity", "").lower()
    parallel = card_info.get("parallel", "").lower()
    number = card_info.get("number", "")

    # Vérifier la rareté
    for rarity_key, mult in RARITY_MULTIPLIERS.items():
        if rarity_key.replace("_", " ") in rarity or rarity_key.replace("_", " ") in parallel:
            multiplier = max(multiplier, mult)

    # Vérifier si numérotée
    if "/" in str(number):
        match = re.search(r'/(\d+)', str(number))
        if match:
            pop = int(match.group(1))
            if pop == 1:
                multiplier *= RARITY_MULTIPLIERS.get("1/1", 50.0)
            elif pop <= 5:
                multiplier *= RARITY_MULTIPLIERS.get("numbered_5", 20.0)
            elif pop <= 10:
                multiplier *= RARITY_MULTIPLIERS.get("numbered_10", 12.0)
            elif pop <= 25:
                multiplier *= RARITY_MULTIPLIERS.get("numbered_25", 8.0)
            elif pop <= 50:
                multiplier *= RARITY_MULTIPLIERS.get("numbered_50", 5.0)
            elif pop <= 99:
                multiplier *= RARITY_MULTIPLIERS.get("numbered_99", 3.5)
            elif pop <= 199:
                multiplier *= RARITY_MULTIPLIERS.get("numbered_199", 2.5)
            elif pop <= 299:
                multiplier *= RARITY_MULTIPLIERS.get("numbered_299", 2.0)
            elif pop <= 499:
                multiplier *= RARITY_MULTIPLIERS.get("numbered_499", 1.5)
            else:
                multiplier *= RARITY_MULTIPLIERS.get("numbered_999", 1.3)

    return multiplier


def calculate_algorithmic_price(card_info: dict, grade: str) -> PriceEstimate:
    """
    Calcule un prix algorithmique basé sur les facteurs pondérés
    Utilisé quand la carte n'est pas dans la base vérifiée
    """
    # Déterminer la catégorie
    game = card_info.get("game", "").lower()
    category = "default"
    for cat in BASE_PRICES.keys():
        if cat in game:
            category = cat
            break

    # Prix de base
    base_price = BASE_PRICES.get(category, BASE_PRICES["default"])

    # Multiplicateur de grade
    grade_mult = GRADE_MULTIPLIERS.get(grade, 1.0)

    # Multiplicateur de joueur/personnage
    player_name = card_info.get("card_name", "")
    tier_name, player_mult = get_player_tier(player_name, category)

    # Multiplicateur de rareté
    rarity_mult = get_rarity_multiplier(card_info)

    # Calcul du prix
    calculated_price = base_price * grade_mult * player_mult * rarity_mult

    # Déterminer la confiance (plus basse pour les cartes complexes)
    confidence = 55
    if tier_name == "unknown":
        confidence -= 15
    if rarity_mult > 5:
        confidence -= 10  # Cartes complexes = moins fiable
    if not card_info.get("set_name"):
        confidence -= 10

    confidence = max(20, min(65, confidence))  # Entre 20% et 65%

    # Appliquer une marge d'erreur de ±30%
    min_price = int(calculated_price * 0.7)
    max_price = int(calculated_price * 1.3)

    # Minimum de $1
    min_price = max(1, min_price)
    max_price = max(2, max_price)

    return PriceEstimate(
        min_price=min_price,
        max_price=max_price,
        confidence=confidence,
        source="algorithm",
        grade=grade,
        card_name=card_info.get("card_name"),
        notes=f"Estimé algorithmiquement (tier: {tier_name})"
    )


def estimate_price(
    game: str,
    card_name: str,
    set_name: str = "",
    number: str = "",
    rarity: str = "",
    grade: str = "RAW"
) -> PriceEstimate:
    """
    Estime le prix d'une carte avec niveau de confiance

    Priorité:
    1. Prix vérifié dans la base (confiance 90%)
    2. Carte similaire trouvée (confiance 60-75%)
    3. Calcul algorithmique (confiance 40-65%)
    4. Non disponible si confiance < 40%
    """
    grade = normalize_grade(grade)

    # 1. Recherche exacte dans la base
    card_id = db_manager.generate_card_id(game, card_name, set_name, number, rarity)
    card_data = db_manager.find_card_exact(card_id)

    if card_data:
        prices = card_data.get("prices", {})
        if grade in prices:
            return PriceEstimate(
                min_price=prices[grade]["min"],
                max_price=prices[grade]["max"],
                confidence=90,
                source="verified",
                grade=grade,
                card_name=card_data.get("name"),
                last_verified=card_data.get("last_verified"),
                notes=card_data.get("notes")
            )

    # 2. Recherche floue (carte similaire)
    similar_card, similarity = db_manager.find_card_fuzzy(game, card_name, set_name, number)

    if similar_card and similarity >= 0.6:
        prices = similar_card.get("prices", {})
        if grade in prices:
            # Confiance proportionnelle à la similarité
            confidence = int(55 + (similarity * 25))  # 55-80%
            return PriceEstimate(
                min_price=prices[grade]["min"],
                max_price=prices[grade]["max"],
                confidence=min(confidence, 75),
                source="similar",
                grade=grade,
                card_name=similar_card.get("name"),
                last_verified=similar_card.get("last_verified"),
                notes=f"Basé sur: {similar_card.get('name', 'carte similaire')}"
            )

    # 3. Calcul algorithmique
    card_info = {
        "game": game,
        "card_name": card_name,
        "set_name": set_name,
        "number": number,
        "rarity": rarity
    }
    algo_estimate = calculate_algorithmic_price(card_info, grade)

    # Si confiance trop basse, retourner "non disponible"
    if algo_estimate.confidence < 40:
        return PriceEstimate(
            min_price=None,
            max_price=None,
            confidence=0,
            source="unavailable",
            grade=grade,
            notes="⚠️ Données insuffisantes - Vérifiez eBay Sold"
        )

    return algo_estimate


def estimate_all_grades(
    game: str,
    card_name: str,
    set_name: str = "",
    number: str = "",
    rarity: str = ""
) -> dict:
    """Estime les prix pour tous les grades standards"""
    grades = ["RAW", "PSA_8", "PSA_9", "PSA_10"]
    return {
        grade: estimate_price(game, card_name, set_name, number, rarity, grade)
        for grade in grades
    }


def format_price_response(estimates: dict) -> str:
    """
    Formate les estimations pour le bot Telegram (Markdown)
    Affiche le niveau de confiance clairement
    """
    lines = []

    # Déterminer la source principale
    sources = [e.source for e in estimates.values() if e.source != "unavailable"]

    if "verified" in sources:
        avg_confidence = 90
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")
        lines.append("💰 **PRIX DE MARCHÉ** ✅ Prix vérifiés")
        lines.append("")
    elif "similar" in sources:
        avg_confidence = 70
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")
        lines.append("💰 **PRIX DE MARCHÉ** 🟡 Carte similaire")
        lines.append("")
    elif "algorithm" in sources:
        avg_confidence = 55
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")
        lines.append("💰 **PRIX ESTIMÉS** ⚠️ Calcul algorithmique")
        lines.append("_Vérifiez sur eBay Sold !_")
        lines.append("")
    else:
        return """━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 **ESTIMATION NON DISPONIBLE**

⚠️ Nous n'avons pas assez de données pour cette carte.

🔎 **Pour connaître le prix réel:**
1. Recherchez sur eBay Sold
2. Consultez CardMarket (Europe)
3. Vérifiez PSA Auction Prices

━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

    # Afficher les prix par grade
    grade_display = {
        "RAW": ("📦", "RAW (non gradée)"),
        "PSA_10": ("🏆", "PSA 10 (Gem Mint)"),
        "PSA_9": ("🥇", "PSA 9 (Mint)"),
        "PSA_8": ("🥈", "PSA 8 (NM-MT)"),
        "PSA_7": ("🥉", "PSA 7 (NM)"),
        "BGS_10": ("💎", "BGS 10 (Pristine)"),
        "BGS_9.5": ("💎", "BGS 9.5 (Gem Mint)")
    }

    grade_order = ["RAW", "PSA_10", "PSA_9", "PSA_8", "PSA_7"]

    for grade in grade_order:
        if grade not in estimates:
            continue
        est = estimates[grade]
        emoji, label = grade_display.get(grade, ("•", grade))

        if est.min_price is not None and est.max_price is not None:
            lines.append(f"{emoji} **{label}**: **${est.min_price:,}** - **${est.max_price:,}**")
        else:
            lines.append(f"{emoji} **{label}**: _Non disponible_")

    lines.append("")
    lines.append(f"📊 Confiance: {avg_confidence}%")

    # Date de vérification si disponible
    verified_est = next((e for e in estimates.values() if e.last_verified), None)
    if verified_est and verified_est.last_verified:
        lines.append(f"📅 Dernière vérification: {verified_est.last_verified}")

    # Note si carte similaire
    similar_est = next((e for e in estimates.values() if e.source == "similar"), None)
    if similar_est and similar_est.notes:
        lines.append(f"📝 {similar_est.notes}")

    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    return "\n".join(lines)


def format_price_for_analysis(
    game: str,
    card_name: str,
    set_name: str = "",
    number: str = "",
    rarity: str = ""
) -> str:
    """
    Génère la section prix à inclure dans l'analyse du bot
    """
    estimates = estimate_all_grades(game, card_name, set_name, number, rarity)
    return format_price_response(estimates)
