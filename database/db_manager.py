"""
Database Manager pour Vaulty Card Analyzer
Gère la base de données des prix vérifiés
"""

import json
import os
import re
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

# Chemin vers la base de données
DB_PATH = Path(__file__).parent / "verified_prices.json"


def load_database() -> dict:
    """Charge la base de données depuis le fichier JSON"""
    if not DB_PATH.exists():
        return {"_metadata": {}, "cards": {}}

    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_database(data: dict) -> None:
    """Sauvegarde la base de données"""
    data["_metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def normalize_id(text: str) -> str:
    """Normalise un texte en ID de carte"""
    # Enlever les caractères spéciaux, garder lettres/chiffres
    normalized = re.sub(r'[^a-z0-9]', '_', text.lower())
    normalized = re.sub(r'_+', '_', normalized).strip('_')
    return normalized


def generate_card_id(game: str, card_name: str, set_name: str, number: str = "", rarity: str = "") -> str:
    """Génère un ID unique pour une carte"""
    parts = [
        normalize_id(game),
        normalize_id(card_name),
        normalize_id(set_name)
    ]
    if number:
        parts.append(normalize_id(number))
    if rarity and rarity.lower() not in ["common", "base"]:
        parts.append(normalize_id(rarity))

    return "_".join(filter(None, parts))


def find_card_exact(card_id: str) -> dict | None:
    """Recherche exacte d'une carte par ID"""
    db = load_database()
    return db.get("cards", {}).get(card_id)


def extract_key_names(text: str) -> set:
    """
    Extrait les noms importants (joueurs, personnages, marques)
    pour un matching plus robuste
    """
    if not text:
        return set()

    text_lower = text.lower()

    # Mots à ignorer (articles, prépositions, génériques)
    stop_words = {
        'the', 'a', 'an', 'of', 'from', 'in', 'at', 'to', 'for', 'and', 'or',
        'de', 'du', 'la', 'le', 'les', 'des', 'un', 'une',
        'base', 'set', 'card', 'cards', 'karte', 'karten',
        'rc', 'rookie', 'auto', 'psa', 'bgs', 'cgc', 'sgc',
        'holo', 'rare', 'common', 'uncommon',
        '2019', '2020', '2021', '2022', '2023', '2024', '2025', '2026',
        'japan', 'japanese', 'english', 'german', 'french'
    }

    # Séparer par espaces et caractères spéciaux
    words = re.split(r'[\s\-_#/,\.()]+', text_lower)

    # Garder les mots significatifs (longueur > 2, pas un stop word)
    key_names = set()
    for word in words:
        word = word.strip()
        if len(word) > 2 and word not in stop_words and not word.isdigit():
            key_names.add(word)

    return key_names


def find_card_fuzzy(game: str, card_name: str, set_name: str = "", number: str = "") -> tuple[dict | None, float]:
    """
    Recherche floue d'une carte avec matching amélioré
    Focus sur le nom du joueur/personnage (plus fiable que le set/année)
    Retourne (carte_trouvée, score_similarité)
    """
    db = load_database()
    cards = db.get("cards", {})

    best_match = None
    best_score = 0.0

    game_lower = game.lower() if game else ""
    card_lower = card_name.lower() if card_name else ""
    set_lower = set_name.lower() if set_name else ""

    # Extraire les mots-clés de la recherche
    search_keywords = extract_key_names(card_name)
    search_keywords.update(extract_key_names(set_name))

    for card_id, card_data in cards.items():
        score = 0.0

        # Match sur le jeu/catégorie (0.15 max)
        db_game = card_data.get("game", "").lower()
        if game_lower and db_game:
            if game_lower in db_game or db_game in game_lower:
                score += 0.15
            # Match partiel (soccer/football)
            elif any(g in game_lower for g in ['soccer', 'football', 'foot']) and \
                 any(g in db_game for g in ['soccer', 'football']):
                score += 0.15

        # Match sur le nom (0.55 max) - POIDS LE PLUS IMPORTANT
        db_name = card_data.get("name", "").lower()
        db_keywords = extract_key_names(db_name)

        if card_lower and db_name:
            # 1. Match exact de mots-clés (noms de joueurs)
            common_keywords = search_keywords & db_keywords
            if common_keywords:
                keyword_score = min(len(common_keywords) * 0.2, 0.4)
                score += keyword_score

            # 2. Match par similarité de séquence (complément)
            name_sim = SequenceMatcher(None, card_lower, db_name).ratio()
            score += name_sim * 0.15

            # 3. Bonus si nom du joueur/personnage contenu exactement
            for keyword in search_keywords:
                if len(keyword) > 3 and keyword in db_name:
                    score += 0.15
                    break

        # Match sur le set (0.15 max) - POIDS RÉDUIT (souvent mal identifié par l'IA)
        db_set = card_data.get("set", "").lower()
        if set_lower and db_set:
            # Match de marque (Topps, Panini, etc.)
            brands = ['topps', 'panini', 'prizm', 'chrome', 'fleer', 'upper deck',
                     'hidden fates', 'base set', 'crown zenith', 'lorcana',
                     'obsidian', 'select', 'mosaic', 'optic', 'donruss']
            for brand in brands:
                if brand in set_lower and brand in db_set:
                    score += 0.1
                    break

            # Match de similarité (faible poids)
            set_sim = SequenceMatcher(None, set_lower, db_set).ratio()
            score += set_sim * 0.05

        # Match sur le numéro (0.1 max)
        db_number = card_data.get("number", "").lower()
        if number and db_number:
            number_clean = number.lower().replace("#", "").strip()
            db_number_clean = db_number.replace("#", "").strip()
            if number_clean and db_number_clean:
                if number_clean == db_number_clean:
                    score += 0.1
                elif number_clean in db_number_clean or db_number_clean in number_clean:
                    score += 0.05

        if score > best_score:
            best_score = score
            best_match = card_data

    # Seuil minimum de 0.4 pour retourner un résultat (abaissé pour plus de flexibilité)
    if best_score >= 0.4:
        return best_match, best_score

    return None, 0.0


def add_price(
    card_id: str,
    name: str,
    game: str,
    set_name: str,
    number: str,
    grade: str,
    min_price: int,
    max_price: int,
    notes: str = ""
) -> bool:
    """Ajoute ou met à jour un prix dans la base"""
    db = load_database()

    # Normaliser le grade
    grade = grade.upper().replace("-", "_").replace(" ", "_")

    if card_id not in db["cards"]:
        db["cards"][card_id] = {
            "name": name,
            "game": game,
            "set": set_name,
            "number": number,
            "prices": {},
            "last_verified": datetime.now().strftime("%Y-%m"),
            "notes": notes
        }

    db["cards"][card_id]["prices"][grade] = {
        "min": min_price,
        "max": max_price
    }
    db["cards"][card_id]["last_verified"] = datetime.now().strftime("%Y-%m")

    if notes:
        db["cards"][card_id]["notes"] = notes

    save_database(db)
    return True


def update_price(card_id: str, grade: str, min_price: int, max_price: int) -> bool:
    """Met à jour un prix existant"""
    db = load_database()

    if card_id not in db["cards"]:
        return False

    grade = grade.upper().replace("-", "_").replace(" ", "_")

    db["cards"][card_id]["prices"][grade] = {
        "min": min_price,
        "max": max_price
    }
    db["cards"][card_id]["last_verified"] = datetime.now().strftime("%Y-%m")

    save_database(db)
    return True


def delete_card(card_id: str) -> bool:
    """Supprime une carte de la base"""
    db = load_database()

    if card_id not in db["cards"]:
        return False

    del db["cards"][card_id]
    save_database(db)
    return True


def list_all_cards() -> list:
    """Liste toutes les cartes dans la base"""
    db = load_database()
    result = []

    for card_id, card_data in db.get("cards", {}).items():
        result.append({
            "id": card_id,
            "name": card_data.get("name", ""),
            "game": card_data.get("game", ""),
            "grades": list(card_data.get("prices", {}).keys()),
            "last_verified": card_data.get("last_verified", "")
        })

    return result


def get_old_prices(months: int = 3) -> list:
    """Retourne les cartes dont les prix n'ont pas été vérifiés depuis X mois"""
    db = load_database()
    old_cards = []

    cutoff = datetime.now()

    for card_id, card_data in db.get("cards", {}).items():
        last_verified = card_data.get("last_verified", "")
        if last_verified:
            try:
                verified_date = datetime.strptime(last_verified, "%Y-%m")
                diff_months = (cutoff.year - verified_date.year) * 12 + (cutoff.month - verified_date.month)
                if diff_months >= months:
                    old_cards.append({
                        "id": card_id,
                        "name": card_data.get("name", ""),
                        "last_verified": last_verified,
                        "months_old": diff_months
                    })
            except ValueError:
                old_cards.append({
                    "id": card_id,
                    "name": card_data.get("name", ""),
                    "last_verified": "unknown",
                    "months_old": 999
                })

    return sorted(old_cards, key=lambda x: x["months_old"], reverse=True)


def get_stats() -> dict:
    """Retourne des statistiques sur la base de données"""
    db = load_database()
    cards = db.get("cards", {})

    games = {}
    total_prices = 0

    for card_data in cards.values():
        game = card_data.get("game", "Unknown")
        games[game] = games.get(game, 0) + 1
        total_prices += len(card_data.get("prices", {}))

    return {
        "total_cards": len(cards),
        "total_prices": total_prices,
        "games": games,
        "last_updated": db.get("_metadata", {}).get("last_updated", "")
    }


def search_cards(query: str, limit: int = 10) -> list:
    """Recherche des cartes par mot-clé"""
    db = load_database()
    results = []
    query_lower = query.lower()

    for card_id, card_data in db.get("cards", {}).items():
        score = 0

        if query_lower in card_data.get("name", "").lower():
            score += 2
        if query_lower in card_data.get("game", "").lower():
            score += 1
        if query_lower in card_data.get("set", "").lower():
            score += 1
        if query_lower in card_id.lower():
            score += 1

        if score > 0:
            results.append((score, card_id, card_data))

    results.sort(reverse=True, key=lambda x: x[0])
    return [(card_id, card_data) for _, card_id, card_data in results[:limit]]
