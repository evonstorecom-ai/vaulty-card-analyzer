"""
Price Estimator pour Vaulty Card Analyzer
Estime les prix avec niveau de confiance basé sur la base de données vérifiée
"""

from dataclasses import dataclass
from typing import Optional
from database import db_manager


@dataclass
class PriceEstimate:
    """Résultat d'une estimation de prix"""
    min_price: Optional[int]
    max_price: Optional[int]
    confidence: int  # 0-100%
    source: str  # "verified", "similar", "unavailable"
    grade: str
    card_name: Optional[str] = None
    notes: Optional[str] = None


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

    Logique:
    - Si carte trouvée exactement → confiance 90%
    - Si carte similaire trouvée → confiance 60%
    - Si rien trouvé → confiance 0%, message "Vérifiez eBay Sold"
    """
    # Normaliser le grade
    grade = grade.upper().replace("-", "_").replace(" ", "_")
    if not grade.startswith(("PSA", "BGS", "CGC", "SGC", "RAW")):
        grade = f"PSA_{grade}" if grade.isdigit() else "RAW"

    # 1. Essayer une recherche exacte par ID généré
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
                notes=card_data.get("notes")
            )
        else:
            # Carte trouvée mais pas ce grade
            available_grades = list(prices.keys())
            return PriceEstimate(
                min_price=None,
                max_price=None,
                confidence=0,
                source="unavailable",
                grade=grade,
                card_name=card_data.get("name"),
                notes=f"Grades disponibles: {', '.join(available_grades)}"
            )

    # 2. Essayer une recherche floue
    similar_card, similarity = db_manager.find_card_fuzzy(game, card_name, set_name, number)

    if similar_card and similarity >= 0.7:
        prices = similar_card.get("prices", {})
        if grade in prices:
            # Ajuster la confiance selon la similarité (60-75%)
            confidence = int(60 + (similarity - 0.7) * 50)
            return PriceEstimate(
                min_price=prices[grade]["min"],
                max_price=prices[grade]["max"],
                confidence=min(confidence, 75),
                source="similar",
                grade=grade,
                card_name=similar_card.get("name"),
                notes=f"Basé sur carte similaire: {similar_card.get('name')}"
            )

    # 3. Aucune donnée trouvée
    return PriceEstimate(
        min_price=None,
        max_price=None,
        confidence=0,
        source="unavailable",
        grade=grade,
        card_name=None,
        notes="Prix variable - Vérifiez eBay Sold"
    )


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


def format_price_response(estimates: dict, include_unavailable: bool = True) -> str:
    """
    Formate les estimations pour le bot Telegram (Markdown)
    """
    lines = []
    has_verified = False
    has_similar = False

    for grade, est in estimates.items():
        if est.source == "verified":
            has_verified = True
        elif est.source == "similar":
            has_similar = True

    # Header selon la source
    if has_verified:
        lines.append("💰 **PRIX VÉRIFIÉS** (Confiance: 90%)")
        lines.append("")
    elif has_similar:
        lines.append("💰 **PRIX ESTIMÉS** (Confiance: ~65%)")
        lines.append("⚠️ _Basé sur carte similaire_")
        lines.append("")
    else:
        return """💰 **ESTIMATION NON DISPONIBLE**

⚠️ Cette carte n'est pas dans notre base de données.

🔎 **Pour connaître le prix réel:**
Recherchez sur eBay Sold (ventes terminées)

📊 Recherche suggérée: "[nom carte] [rareté] sold" sur eBay"""

    # Afficher les prix
    grade_emojis = {
        "RAW": "📦",
        "PSA_7": "🥉",
        "PSA_8": "🥈",
        "PSA_9": "🥇",
        "PSA_10": "🏆",
        "BGS_9": "🥇",
        "BGS_9.5": "🏆",
        "BGS_10": "💎"
    }

    for grade, est in estimates.items():
        emoji = grade_emojis.get(grade, "•")
        grade_display = grade.replace("_", " ")

        if est.min_price is not None and est.max_price is not None:
            lines.append(f"{emoji} **{grade_display}**: ${est.min_price} - ${est.max_price}")
        elif include_unavailable:
            lines.append(f"{emoji} **{grade_display}**: _Non disponible_")

    # Footer
    lines.append("")
    lines.append("🔎 **Vérifiez toujours sur eBay Sold !**")

    if has_similar:
        lines.append("")
        lines.append(f"_Note: {list(estimates.values())[0].notes}_")

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
