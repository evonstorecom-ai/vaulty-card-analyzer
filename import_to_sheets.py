"""
Script d'import unique — à lancer UNE SEULE FOIS
Transfère les données de vaulty_database.json vers Google Sheets
"""
import json
from vaulty_database_sheets import add_to_database

with open("vaulty_database.json", encoding="utf-8") as f:
    db = json.load(f)

cards = db.get("cards", [])
print(f"📦 {len(cards)} cartes à importer...\n")

for i, card in enumerate(cards, 1):
    add_to_database(
        card_info=card,
        sale_price=card.get("sale_price", 0),
        currency=card.get("currency", "CHF"),
    )
    print(f"  [{i}/{len(cards)}] ✅ {card.get('player_name')} — {card.get('sale_price')} {card.get('currency','CHF')}")

print(f"\n✅ Import terminé ! {len(cards)} cartes dans Google Sheets.")
