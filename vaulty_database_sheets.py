"""
VAULTY PROTOCOL — Base de données Google Sheets
Remplace vaulty_database.json par un Google Sheets persistant.

Avantages :
- Données jamais perdues (même si Railway redéploie)
- Tu vois tout depuis Google Sheets sur mobile
- Tu peux modifier les prix à la main
- Historique des modifications automatique

Setup : voir README_vaulty_bot.md section "Google Sheets"
"""

import os
import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# ─── CONFIGURATION ────────────────────────────────────────────────────────────

SPREADSHEET_ID  = os.environ.get("GOOGLE_SHEET_ID", "")
SHEET_NAME      = "Ventes Vaulty"

# Colonnes du tableau (ordre exact)
COLUMNS = [
    "Date",
    "Joueur / Carte",
    "Sport / Jeu",
    "Set",
    "Année",
    "Numéro",
    "Variante",
    "Grading",
    "Grade",
    "Tirage",
    "Rookie",
    "Prix CHF",
    "Devise",
    "Cert ID",
    "Score Confiance",
    "Notes",
    "Source",
]

# ─── CONNEXION GOOGLE SHEETS ──────────────────────────────────────────────────

def _get_sheet():
    """
    Connexion au Google Sheets.
    Les credentials viennent de la variable d'env GOOGLE_CREDENTIALS_JSON
    (le contenu du fichier credentials.json en une seule ligne)
    """
    creds_raw = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")
    if not creds_raw:
        raise EnvironmentError(
            "❌ Variable GOOGLE_CREDENTIALS_JSON manquante.\n"
            "Voir le README pour la configuration Google Sheets."
        )

    creds_dict = json.loads(creds_raw)
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds  = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_key(SPREADSHEET_ID)

    # Créer l'onglet s'il n'existe pas
    try:
        sheet = spreadsheet.worksheet(SHEET_NAME)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows=1000, cols=len(COLUMNS))
        # Ajouter les en-têtes
        sheet.append_row(COLUMNS)
        # Mettre les en-têtes en gras
        sheet.format("A1:Q1", {
            "textFormat": {"bold": True},
            "backgroundColor": {"red": 0.04, "green": 0.055, "blue": 0.078},
        })

    return sheet


# ─── LECTURE BDD ──────────────────────────────────────────────────────────────

def load_database() -> dict:
    """
    Charge toutes les ventes depuis Google Sheets.
    Retourne le même format que l'ancien vaulty_database.json
    pour assurer la compatibilité.
    """
    try:
        sheet   = _get_sheet()
        records = sheet.get_all_records()  # liste de dicts avec les en-têtes comme clés

        cards = []
        for row in records:
            if not row.get("Joueur / Carte"):
                continue  # ignorer les lignes vides
            cards.append({
                "player_name":      row.get("Joueur / Carte", ""),
                "sport_or_game":    row.get("Sport / Jeu", ""),
                "card_set":         row.get("Set", ""),
                "year":             str(row.get("Année", "")),
                "card_number":      str(row.get("Numéro", "")),
                "parallel":         row.get("Variante", "") or None,
                "grading_company":  row.get("Grading", "RAW"),
                "grade":            str(row.get("Grade", "")) or None,
                "print_run":        row.get("Tirage", "") or None,
                "rookie_card":      str(row.get("Rookie", "")).upper() == "OUI",
                "sale_price":       _to_float(row.get("Prix CHF")),
                "currency":         row.get("Devise", "CHF"),
                "sale_date":        str(row.get("Date", "")),
                "cert_id":          row.get("Cert ID", "") or None,
                "notes":            row.get("Notes", "") or None,
                "source":           row.get("Source", "vaulty_sale"),
            })

        return {
            "cards": cards,
            "last_updated": datetime.now().isoformat(),
            "total": len(cards),
            "source": "google_sheets",
        }

    except Exception as e:
        print(f"⚠️ Erreur lecture Google Sheets : {e}")
        # Fallback sur fichier local si dispo
        return _load_local_fallback()


def _to_float(val) -> float | None:
    if val is None or val == "":
        return None
    try:
        return float(str(val).replace(",", ".").replace(" ", ""))
    except Exception:
        return None


# ─── ÉCRITURE BDD ─────────────────────────────────────────────────────────────

def add_to_database(card_info: dict, sale_price: float, currency: str = "CHF") -> None:
    """
    Ajoute une nouvelle vente dans Google Sheets.
    Une ligne = une carte vendue.
    """
    try:
        sheet = _get_sheet()

        row = [
            datetime.now().strftime("%Y-%m-%d"),               # Date
            card_info.get("player_name", ""),                  # Joueur / Carte
            card_info.get("sport_or_game", ""),                # Sport / Jeu
            card_info.get("card_set", ""),                     # Set
            card_info.get("year", ""),                         # Année
            card_info.get("card_number", ""),                  # Numéro
            card_info.get("parallel", "") or "",               # Variante
            card_info.get("grading_company", "RAW"),           # Grading
            card_info.get("grade", "") or "",                  # Grade
            card_info.get("print_run", "") or "",              # Tirage
            "OUI" if card_info.get("rookie_card") else "NON",  # Rookie
            sale_price,                                        # Prix CHF
            currency,                                          # Devise
            card_info.get("cert_id", "") or "",                # Cert ID
            card_info.get("confidence", "MEDIUM"),             # Score Confiance
            card_info.get("notes", "") or "",                  # Notes
            "vaulty_sale",                                     # Source
        ]

        sheet.append_row(row, value_input_option="USER_ENTERED")
        print(f"✅ Ajouté dans Google Sheets : {card_info.get('player_name')} — {sale_price} {currency}")

    except Exception as e:
        print(f"⚠️ Erreur écriture Google Sheets : {e}")
        # Fallback : sauvegarder localement
        _save_local_fallback(card_info, sale_price, currency)


# ─── RECHERCHE DANS LA BDD ────────────────────────────────────────────────────

def search_in_database(card_info: dict) -> list[dict]:
    """
    Cherche des cartes similaires dans la BDD Google Sheets.
    Système de score de matching (sur 100).
    """
    db      = load_database()
    results = []

    player_name = card_info.get("player_name", "").lower()
    card_set    = card_info.get("card_set", "").lower()
    card_year   = str(card_info.get("year", ""))
    grade       = str(card_info.get("grade", "")).lower()
    grading_co  = card_info.get("grading_company", "").lower()

    for card in db.get("cards", []):
        score = 0
        c = {k: str(v).lower() if v else "" for k, v in card.items()}

        if player_name and player_name in c.get("player_name", ""):
            score += 40
        if card_set and any(w in c.get("card_set", "") for w in card_set.split() if len(w) > 3):
            score += 25
        if card_year and card_year in c.get("year", ""):
            score += 15
        if grade and grade in c.get("grade", ""):
            score += 12
        if grading_co and grading_co in c.get("grading_company", ""):
            score += 8

        if score >= 40:
            results.append({**card, "_match_score": score})

    results.sort(key=lambda x: x["_match_score"], reverse=True)
    return results[:5]


# ─── STATS BDD ────────────────────────────────────────────────────────────────

def get_stats() -> dict:
    """Retourne les statistiques de la BDD pour /stats."""
    db    = load_database()
    cards = db.get("cards", [])

    if not cards:
        return {"total": 0}

    prices = [c.get("sale_price") for c in cards if c.get("sale_price")]
    sports = {}
    for c in cards:
        s = c.get("sport_or_game", "Inconnu")
        sports[s] = sports.get(s, 0) + 1

    return {
        "total":       len(cards),
        "total_sales": sum(p for p in prices if p),
        "avg_price":   round(sum(prices) / len(prices), 0) if prices else 0,
        "max_price":   max(prices) if prices else 0,
        "min_price":   min(prices) if prices else 0,
        "sports":      dict(sorted(sports.items(), key=lambda x: x[1], reverse=True)),
        "last_sale":   max((c.get("sale_date", "") for c in cards), default="N/A"),
        "sheet_url":   f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}",
    }


# ─── FALLBACK LOCAL ───────────────────────────────────────────────────────────

LOCAL_FALLBACK = "vaulty_database_local.json"

def _load_local_fallback() -> dict:
    """Charge le fichier JSON local en cas d'erreur Google Sheets."""
    from pathlib import Path
    path = Path(LOCAL_FALLBACK)
    if not path.exists():
        return {"cards": [], "last_updated": None, "source": "local_fallback"}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        data["source"] = "local_fallback"
        return data

def _save_local_fallback(card_info: dict, sale_price: float, currency: str) -> None:
    """Sauvegarde en JSON local si Google Sheets est inaccessible."""
    from pathlib import Path
    path = Path(LOCAL_FALLBACK)
    db   = _load_local_fallback()
    db["cards"].append({
        **card_info,
        "sale_price": sale_price,
        "currency":   currency,
        "sale_date":  datetime.now().strftime("%Y-%m-%d"),
        "source":     "local_fallback_offline",
    })
    db["last_updated"] = datetime.now().isoformat()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    print(f"⚠️ Sauvegardé en local (fallback) : {LOCAL_FALLBACK}")
