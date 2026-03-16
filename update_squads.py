#!/usr/bin/env python3
"""
Script de mise à jour automatique des effectifs Ligue 1 depuis API-Football.

Utilise les endpoints:
- /teams?league=61&season=2025  → liste des équipes Ligue 1
- /players/squads?team={id}     → effectif actuel de chaque équipe
- /coachs?team={id}             → coach actuel

Usage:
    python update_squads.py                   # Met à jour tous les effectifs
    python update_squads.py --team ol         # Met à jour uniquement Lyon
    python update_squads.py --dry-run         # Affiche sans modifier le fichier
    python update_squads.py --dump-json       # Exporte en JSON brut (debug)

Nécessite: API_FOOTBALL_KEY en variable d'environnement
"""

import asyncio
import aiohttp
import json
import os
import sys
import argparse
from datetime import datetime


API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "")
API_FOOTBALL_HOST = "v3.football.api-sports.io"
API_FOOTBALL_BASE = f"https://{API_FOOTBALL_HOST}"
LIGUE1_LEAGUE_ID = 61
CURRENT_SEASON = 2025

# Mapping position API-Football → notre format
POS_MAP = {
    "Goalkeeper": "GK",
    "Defender": "DEF",
    "Midfielder": "MID",
    "Attacker": "FWD",
}

# Mapping position détaillée (basé sur le nom de position dans l'API)
DETAILED_POS_MAP = {
    "Goalkeeper": None,  # Pas de sous-position pour GK
    "Defender": "DC",
    "Midfielder": "MC",
    "Attacker": "BU",
}


async def api_request(session: aiohttp.ClientSession, endpoint: str, params: dict = None) -> dict:
    """Requête vers API-Football avec gestion d'erreurs."""
    if not API_FOOTBALL_KEY:
        print("ERREUR: Variable d'environnement API_FOOTBALL_KEY non définie!")
        print("Définissez-la avec: export API_FOOTBALL_KEY=votre_cle_api")
        sys.exit(1)

    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    url = f"{API_FOOTBALL_BASE}/{endpoint}"

    try:
        async with session.get(url, headers=headers, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                # Vérifier les erreurs API
                errors = data.get("errors", {})
                if errors:
                    print(f"  ⚠ Erreur API pour {endpoint}: {errors}")
                    return {"response": []}
                return data
            elif resp.status == 429:
                print("  ⚠ Rate limit atteint, attente 60s...")
                await asyncio.sleep(60)
                return await api_request(session, endpoint, params)
            else:
                print(f"  ⚠ Erreur HTTP {resp.status} pour {endpoint}")
                return {"response": []}
    except Exception as e:
        print(f"  ⚠ Erreur réseau: {e}")
        return {"response": []}


async def get_ligue1_teams(session: aiohttp.ClientSession) -> list[dict]:
    """Récupère toutes les équipes de Ligue 1 pour la saison en cours."""
    print(f"Récupération des équipes Ligue 1 saison {CURRENT_SEASON}...")
    data = await api_request(session, "teams", {
        "league": LIGUE1_LEAGUE_ID,
        "season": CURRENT_SEASON,
    })

    teams = []
    for item in data.get("response", []):
        team = item.get("team", {})
        venue = item.get("venue", {})
        teams.append({
            "id": team.get("id"),
            "name": team.get("name", ""),
            "code": team.get("code", ""),
            "logo": team.get("logo", ""),
            "venue_name": venue.get("name", ""),
            "venue_city": venue.get("city", ""),
        })

    print(f"  {len(teams)} équipes trouvées")
    return teams


async def get_squad(session: aiohttp.ClientSession, team_id: int, team_name: str) -> list[dict]:
    """Récupère l'effectif actuel d'une équipe."""
    data = await api_request(session, "players/squads", {"team": team_id})

    players = []
    for team_data in data.get("response", []):
        for player in team_data.get("players", []):
            pos_api = player.get("position", "Midfielder")
            pos_group = POS_MAP.get(pos_api, "MID")

            player_data = {
                "name": player.get("name", ""),
                "number": player.get("number") or 0,
                "rating": 75,  # Rating par défaut, sera ajusté
                "age": player.get("age", 0),
            }

            # Ajouter la position détaillée pour DEF/MID/FWD
            if pos_group != "GK":
                player_data["position"] = DETAILED_POS_MAP.get(pos_api, "MC")

            players.append({
                "group": pos_group,
                **player_data,
            })

    print(f"  {team_name}: {len(players)} joueurs récupérés")
    return players


async def get_coach(session: aiohttp.ClientSession, team_id: int) -> str:
    """Récupère le coach actuel d'une équipe."""
    data = await api_request(session, "coachs", {"team": team_id})

    for coach in data.get("response", []):
        career = coach.get("career", [])
        for stint in career:
            if stint.get("team", {}).get("id") == team_id and stint.get("end") is None:
                return coach.get("name", "")
    return ""


async def get_player_ratings(session: aiohttp.ClientSession, team_id: int) -> dict[str, int]:
    """
    Récupère les ratings des joueurs via les statistiques de la saison en cours.
    Endpoint: /players?team={id}&league=61&season=2025
    """
    data = await api_request(session, "players", {
        "team": team_id,
        "league": LIGUE1_LEAGUE_ID,
        "season": CURRENT_SEASON,
    })

    ratings = {}
    for item in data.get("response", []):
        player = item.get("player", {})
        stats = item.get("statistics", [])
        if stats:
            # Prendre le rating moyen de la saison
            rating_str = stats[0].get("games", {}).get("rating")
            if rating_str:
                try:
                    rating = round(float(rating_str) * 10)  # Convertir 7.2 → 72
                    rating = min(95, max(60, rating))  # Borner entre 60-95
                    ratings[player.get("name", "")] = rating
                except (ValueError, TypeError):
                    pass
    return ratings


def build_squad_dict(players: list[dict], ratings: dict[str, int]) -> dict:
    """Organise les joueurs en dict par position pour ligue1_teams.py."""
    squad = {"GK": [], "DEF": [], "MID": [], "FWD": []}

    for player in players:
        group = player.pop("group", "MID")
        if group not in squad:
            group = "MID"

        # Appliquer le rating réel si disponible
        name = player["name"]
        if name in ratings:
            player["rating"] = ratings[name]

        squad[group].append(player)

    # Trier par rating décroissant dans chaque groupe
    for group in squad:
        squad[group].sort(key=lambda x: x.get("rating", 75), reverse=True)

    return squad


def build_default_xi(squad: dict, formation: str = "4-3-3") -> dict:
    """Construit le XI par défaut basé sur les meilleurs joueurs par poste."""
    formations = {
        "4-3-3": {"GK": 1, "DEF": 4, "MID": 3, "FWD": 3},
        "4-4-2": {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2},
        "4-2-3-1": {"GK": 1, "DEF": 4, "MID": 5, "FWD": 1},
        "3-4-3": {"GK": 1, "DEF": 3, "MID": 4, "FWD": 3},
        "3-5-2": {"GK": 1, "DEF": 3, "MID": 5, "FWD": 2},
        "3-4-1-2": {"GK": 1, "DEF": 3, "MID": 5, "FWD": 2},
    }
    slots = formations.get(formation, {"GK": 1, "DEF": 4, "MID": 3, "FWD": 3})

    lineup = []
    for group, count in slots.items():
        players = squad.get(group, [])
        for p in players[:count]:
            # Utiliser le nom de famille pour le XI (plus court)
            name = p["name"]
            parts = name.split()
            short_name = parts[-1] if len(parts) > 1 else name
            lineup.append(short_name)

    return {
        "formation": formation,
        "lineup": lineup,
    }


def format_squad_python(team_key: str, team_data: dict) -> str:
    """Formate les données d'une équipe en code Python pour ligue1_teams.py."""
    indent = "    "

    lines = [f'{indent}"{team_key}": {{']
    lines.append(f'{indent}    "full_name": "{team_data["full_name"]}",')
    lines.append(f'{indent}    "short_name": "{team_data["short_name"]}",')
    lines.append(f'{indent}    "city": "{team_data["city"]}",')
    lines.append(f'{indent}    "stadium": "{team_data["stadium"]}",')
    lines.append(f'{indent}    "coach": "{team_data["coach"]}",')
    lines.append(f'{indent}    "api_football_id": {team_data["api_football_id"]},')
    lines.append(f'{indent}    "preferred_formations": {json.dumps(team_data["preferred_formations"])},')
    lines.append(f'{indent}    "style": "{team_data["style"]}",')

    # Squad
    lines.append(f'{indent}    "squad": {{')
    for group in ["GK", "DEF", "MID", "FWD"]:
        lines.append(f'{indent}        "{group}": [')
        for p in team_data["squad"].get(group, []):
            parts = []
            parts.append(f'"name": "{p["name"]}"')
            parts.append(f'"number": {p["number"]}')
            parts.append(f'"rating": {p["rating"]}')
            if "position" in p:
                parts.append(f'"position": "{p["position"]}"')
            parts.append(f'"age": {p["age"]}')
            lines.append(f'{indent}            {{{", ".join(parts)}}},')
        lines.append(f'{indent}        ],')
    lines.append(f'{indent}    }},')

    # Default XI
    xi = team_data["default_xi"]
    lines.append(f'{indent}    "default_xi": {{')
    lines.append(f'{indent}        "formation": "{xi["formation"]}",')
    lines.append(f'{indent}        "lineup": {json.dumps(xi["lineup"])}')
    lines.append(f'{indent}    }}')
    lines.append(f'{indent}}},')

    return "\n".join(lines)


async def update_single_team(session: aiohttp.ClientSession, team_key: str, team_id: int, existing_data: dict) -> dict | None:
    """Met à jour les données d'une seule équipe depuis l'API."""
    team_name = existing_data.get("full_name", team_key)
    print(f"\n--- Mise à jour: {team_name} (ID: {team_id}) ---")

    # Récupérer effectif, coach, et ratings en parallèle
    squad_task = get_squad(session, team_id, team_name)
    coach_task = get_coach(session, team_id)
    ratings_task = get_player_ratings(session, team_id)

    players, coach_name, ratings = await asyncio.gather(squad_task, coach_task, ratings_task)

    if not players:
        print(f"  ✗ Aucun joueur récupéré pour {team_name}, skip")
        return None

    # Construire le nouveau squad
    squad = build_squad_dict(players, ratings)

    # Garder les formations existantes et le style
    formation = existing_data.get("preferred_formations", ["4-3-3"])[0]
    default_xi = build_default_xi(squad, formation)

    updated = {
        "full_name": existing_data.get("full_name", team_name),
        "short_name": existing_data.get("short_name", team_key.upper()),
        "city": existing_data.get("city", ""),
        "stadium": existing_data.get("stadium", ""),
        "coach": coach_name or existing_data.get("coach", ""),
        "api_football_id": team_id,
        "preferred_formations": existing_data.get("preferred_formations", ["4-3-3"]),
        "style": existing_data.get("style", ""),
        "squad": squad,
        "default_xi": default_xi,
    }

    # Résumé
    total = sum(len(v) for v in squad.values())
    print(f"  ✓ {total} joueurs | Coach: {updated['coach']} | Formation: {formation}")
    print(f"  ✓ XI: {', '.join(default_xi['lineup'])}")

    return updated


async def main():
    parser = argparse.ArgumentParser(description="Mise à jour des effectifs Ligue 1 depuis API-Football")
    parser.add_argument("--team", type=str, help="Clé de l'équipe à mettre à jour (ex: ol, psg)")
    parser.add_argument("--dry-run", action="store_true", help="Afficher sans modifier le fichier")
    parser.add_argument("--dump-json", action="store_true", help="Exporter les données brutes en JSON")
    args = parser.parse_args()

    if not API_FOOTBALL_KEY:
        print("=" * 60)
        print("ERREUR: API_FOOTBALL_KEY non configurée!")
        print("")
        print("Pour obtenir une clé API-Football:")
        print("  1. Inscrivez-vous sur https://www.api-football.com/")
        print("  2. Récupérez votre clé API dans le dashboard")
        print("  3. Exportez-la: export API_FOOTBALL_KEY=votre_cle")
        print("")
        print("Le plan gratuit offre 100 requêtes/jour.")
        print("=" * 60)
        sys.exit(1)

    # Charger les données existantes
    from ligue1_teams import LIGUE1_TEAMS

    print(f"=" * 60)
    print(f"MISE À JOUR DES EFFECTIFS LIGUE 1 - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"Saison: {CURRENT_SEASON}")
    print(f"=" * 60)

    async with aiohttp.ClientSession() as session:
        # Vérifier d'abord le quota API
        status_data = await api_request(session, "status", {})
        if status_data.get("response"):
            account = status_data["response"].get("account", {})
            requests_info = status_data["response"].get("requests", {})
            print(f"Compte: {account.get('firstname', '')} {account.get('lastname', '')}")
            print(f"Plan: {status_data['response'].get('subscription', {}).get('plan', 'N/A')}")
            print(f"Requêtes: {requests_info.get('current', '?')}/{requests_info.get('limit_day', '?')} aujourd'hui")

        updated_teams = {}

        if args.team:
            # Mise à jour d'une seule équipe
            team_key = args.team.lower()
            if team_key not in LIGUE1_TEAMS:
                print(f"Équipe '{team_key}' non trouvée. Équipes disponibles: {', '.join(LIGUE1_TEAMS.keys())}")
                sys.exit(1)

            team_data = LIGUE1_TEAMS[team_key]
            team_id = team_data["api_football_id"]
            result = await update_single_team(session, team_key, team_id, team_data)
            if result:
                updated_teams[team_key] = result
        else:
            # Mise à jour de toutes les équipes
            for team_key, team_data in LIGUE1_TEAMS.items():
                team_id = team_data["api_football_id"]
                result = await update_single_team(session, team_key, team_id, team_data)
                if result:
                    updated_teams[team_key] = result
                # Petite pause pour éviter le rate limit
                await asyncio.sleep(1)

    if not updated_teams:
        print("\nAucune équipe mise à jour.")
        return

    # Export JSON si demandé
    if args.dump_json:
        output_file = "squads_dump.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(updated_teams, f, ensure_ascii=False, indent=2)
        print(f"\nDonnées exportées dans {output_file}")

    if args.dry_run:
        print("\n[DRY RUN] Voici ce qui serait écrit:")
        for key, data in updated_teams.items():
            print(f"\n{format_squad_python(key, data)}")
        return

    # Réécrire ligue1_teams.py avec les données mises à jour
    _write_teams_file(LIGUE1_TEAMS, updated_teams)

    print(f"\n{'=' * 60}")
    print(f"✓ {len(updated_teams)} équipe(s) mise(s) à jour dans ligue1_teams.py")
    print(f"{'=' * 60}")


def _write_teams_file(original_teams: dict, updated_teams: dict):
    """Réécrit ligue1_teams.py avec les équipes mises à jour."""
    # Fusionner: garder les originaux et remplacer les mis à jour
    all_teams = {}
    for key in original_teams:
        if key in updated_teams:
            all_teams[key] = updated_teams[key]
        else:
            all_teams[key] = original_teams[key]

    # Lire le fichier existant pour récupérer les fonctions en bas
    teams_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ligue1_teams.py")
    with open(teams_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Trouver où commencent les fonctions/aliases (après le dict LIGUE1_TEAMS)
    # On cherche "# Aliases" ou "TEAM_ALIASES"
    suffix_marker = "# Aliases"
    suffix_idx = content.find(suffix_marker)
    if suffix_idx == -1:
        suffix_marker = "TEAM_ALIASES"
        suffix_idx = content.find(suffix_marker)

    suffix = ""
    if suffix_idx != -1:
        suffix = "\n" + content[suffix_idx:]

    # Écrire le nouveau fichier
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    lines = [
        '"""',
        f'Base de données des {len(all_teams)} équipes de Ligue 1 {CURRENT_SEASON}-{CURRENT_SEASON + 1}',
        f'Dernière mise à jour depuis API-Football: {now}',
        'Contient les effectifs, formations préférées, et informations des coachs.',
        '"""',
        '',
        'LIGUE1_TEAMS = {',
    ]

    for key, data in all_teams.items():
        lines.append(format_squad_python(key, data))

    lines.append("}")
    lines.append("")

    output = "\n".join(lines)
    if suffix:
        output += suffix

    with open(teams_file, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"  Fichier {teams_file} mis à jour")


if __name__ == "__main__":
    asyncio.run(main())
