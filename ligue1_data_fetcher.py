"""
Module de récupération des données en temps réel pour le bot Ligue 1.
Utilise API-Football et The Odds API pour obtenir:
- Blessures et suspensions
- Forme des joueurs
- Cotes des bookmakers
- Prochains matchs
"""

import aiohttp
import asyncio
import os
import json
from datetime import datetime, timedelta


# Configuration API
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "")
API_FOOTBALL_HOST = "v3.football.api-sports.io"
API_FOOTBALL_BASE = f"https://{API_FOOTBALL_HOST}"

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
ODDS_API_BASE = "https://api.the-odds-api.com/v4"

# Ligue 1 ID dans API-Football
LIGUE1_LEAGUE_ID = 61
CURRENT_SEASON = 2025


class Ligue1DataFetcher:
    """Récupère les données en temps réel pour les prédictions Ligue 1."""

    def __init__(self):
        self.api_football_key = API_FOOTBALL_KEY
        self.odds_api_key = ODDS_API_KEY
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes

    def _get_cache(self, key: str):
        if key in self._cache:
            data, timestamp = self._cache[key]
            if (datetime.now() - timestamp).seconds < self._cache_ttl:
                return data
        return None

    def _set_cache(self, key: str, data):
        self._cache[key] = (data, datetime.now())

    async def _api_football_request(self, endpoint: str, params: dict = None) -> dict:
        """Requête vers API-Football."""
        if not self.api_football_key:
            return {"error": "API_FOOTBALL_KEY non configurée. Définissez la variable d'environnement."}

        cache_key = f"apifb_{endpoint}_{json.dumps(params or {}, sort_keys=True)}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        headers = {
            "x-apisports-key": self.api_football_key,
        }
        url = f"{API_FOOTBALL_BASE}/{endpoint}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self._set_cache(cache_key, data)
                        return data
                    else:
                        return {"error": f"API-Football erreur {resp.status}"}
        except Exception as e:
            return {"error": str(e)}

    async def _odds_api_request(self, endpoint: str, params: dict = None) -> dict:
        """Requête vers The Odds API."""
        if not self.odds_api_key:
            return {"error": "ODDS_API_KEY non configurée. Définissez la variable d'environnement."}

        cache_key = f"odds_{endpoint}_{json.dumps(params or {}, sort_keys=True)}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        url = f"{ODDS_API_BASE}/{endpoint}"
        params = params or {}
        params["apiKey"] = self.odds_api_key

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self._set_cache(cache_key, data)
                        return data
                    else:
                        return {"error": f"Odds API erreur {resp.status}"}
        except Exception as e:
            return {"error": str(e)}

    async def get_injuries(self, team_id: int) -> list[dict]:
        """Récupère les blessures et suspensions d'une équipe."""
        data = await self._api_football_request("injuries", {
            "league": LIGUE1_LEAGUE_ID,
            "season": CURRENT_SEASON,
            "team": team_id,
        })

        if "error" in data:
            return []

        injuries = []
        for item in data.get("response", []):
            player = item.get("player", {})
            team = item.get("team", {})
            fixture = item.get("fixture", {})
            injuries.append({
                "player_name": player.get("name", "Inconnu"),
                "type": player.get("type", "Inconnu"),  # "Missing Fixture" / "Questionable"
                "reason": player.get("reason", "Inconnu"),
                "team": team.get("name", ""),
                "fixture_date": fixture.get("date", ""),
            })
        return injuries

    async def get_team_stats(self, team_id: int) -> dict:
        """Récupère les statistiques de l'équipe pour la saison en cours."""
        data = await self._api_football_request("teams/statistics", {
            "league": LIGUE1_LEAGUE_ID,
            "season": CURRENT_SEASON,
            "team": team_id,
        })

        if "error" in data:
            return {}

        response = data.get("response", {})
        return {
            "form": response.get("form", ""),
            "fixtures": response.get("fixtures", {}),
            "goals": response.get("goals", {}),
            "clean_sheets": response.get("clean_sheet", {}),
            "lineups": response.get("lineups", []),
        }

    async def get_next_fixtures(self, team_id: int, count: int = 3) -> list[dict]:
        """Récupère les prochains matchs d'une équipe."""
        data = await self._api_football_request("fixtures", {
            "league": LIGUE1_LEAGUE_ID,
            "season": CURRENT_SEASON,
            "team": team_id,
            "next": count,
        })

        if "error" in data:
            return []

        fixtures = []
        for item in data.get("response", []):
            fixture = item.get("fixture", {})
            teams = item.get("teams", {})
            fixtures.append({
                "id": fixture.get("id"),
                "date": fixture.get("date", ""),
                "venue": fixture.get("venue", {}).get("name", ""),
                "home_team": teams.get("home", {}).get("name", ""),
                "home_id": teams.get("home", {}).get("id"),
                "away_team": teams.get("away", {}).get("name", ""),
                "away_id": teams.get("away", {}).get("id"),
            })
        return fixtures

    async def get_last_results(self, team_id: int, count: int = 5) -> list[dict]:
        """Récupère les derniers résultats d'une équipe."""
        data = await self._api_football_request("fixtures", {
            "league": LIGUE1_LEAGUE_ID,
            "season": CURRENT_SEASON,
            "team": team_id,
            "last": count,
        })

        if "error" in data:
            return []

        results = []
        for item in data.get("response", []):
            fixture = item.get("fixture", {})
            teams = item.get("teams", {})
            goals = item.get("goals", {})
            results.append({
                "date": fixture.get("date", ""),
                "home_team": teams.get("home", {}).get("name", ""),
                "away_team": teams.get("away", {}).get("name", ""),
                "home_goals": goals.get("home", 0),
                "away_goals": goals.get("away", 0),
                "home_winner": teams.get("home", {}).get("winner"),
                "away_winner": teams.get("away", {}).get("winner"),
            })
        return results

    async def get_predictions(self, fixture_id: int) -> dict:
        """Récupère les prédictions API-Football pour un match."""
        data = await self._api_football_request("predictions", {
            "fixture": fixture_id,
        })

        if "error" in data:
            return {}

        if data.get("response"):
            pred = data["response"][0]
            return {
                "winner": pred.get("predictions", {}).get("winner", {}),
                "win_or_draw": pred.get("predictions", {}).get("win_or_draw"),
                "goals_home": pred.get("predictions", {}).get("goals", {}).get("home"),
                "goals_away": pred.get("predictions", {}).get("goals", {}).get("away"),
                "advice": pred.get("predictions", {}).get("advice", ""),
                "percent": pred.get("predictions", {}).get("percent", {}),
                "comparison": pred.get("comparison", {}),
            }
        return {}

    async def get_odds(self, home_team: str = None, away_team: str = None) -> list[dict]:
        """Récupère les cotes pour les matchs de Ligue 1 depuis The Odds API."""
        data = await self._odds_api_request(
            "sports/soccer_france_ligue_one/odds",
            {
                "regions": "eu,uk",
                "markets": "h2h,totals",
                "oddsFormat": "decimal",
            }
        )

        if isinstance(data, dict) and "error" in data:
            return []

        if not isinstance(data, list):
            return []

        odds_list = []
        for event in data:
            event_home = event.get("home_team", "")
            event_away = event.get("away_team", "")

            # Filtrer par équipe si spécifié
            if home_team and home_team.lower() not in event_home.lower() and \
               home_team.lower() not in event_away.lower():
                if away_team and away_team.lower() not in event_home.lower() and \
                   away_team.lower() not in event_away.lower():
                    continue

            bookmakers = []
            for bm in event.get("bookmakers", []):
                markets = {}
                for market in bm.get("markets", []):
                    if market["key"] == "h2h":
                        outcomes = {o["name"]: o["price"] for o in market.get("outcomes", [])}
                        markets["h2h"] = outcomes
                    elif market["key"] == "totals":
                        for o in market.get("outcomes", []):
                            markets[f"totals_{o['name'].lower()}_{o.get('point', 2.5)}"] = o["price"]

                bookmakers.append({
                    "name": bm.get("title", ""),
                    "markets": markets,
                })

            odds_list.append({
                "home_team": event_home,
                "away_team": event_away,
                "commence_time": event.get("commence_time", ""),
                "bookmakers": bookmakers,
            })

        return odds_list

    async def get_best_odds(self, home_team: str, away_team: str, top_n: int = 4) -> dict:
        """Récupère les meilleures cotes pour un match (top N bookmakers)."""
        all_odds = await self.get_odds(home_team, away_team)

        if not all_odds:
            return self._generate_simulated_odds(home_team, away_team, top_n)

        best = {
            "home_win": [],
            "draw": [],
            "away_win": [],
            "over_2_5": [],
            "under_2_5": [],
        }

        for event in all_odds:
            for bm in event.get("bookmakers", []):
                markets = bm.get("markets", {})
                name = bm["name"]

                if "h2h" in markets:
                    h2h = markets["h2h"]
                    if event["home_team"] in h2h:
                        best["home_win"].append({"bookmaker": name, "odds": h2h[event["home_team"]]})
                    if "Draw" in h2h:
                        best["draw"].append({"bookmaker": name, "odds": h2h["Draw"]})
                    if event["away_team"] in h2h:
                        best["away_win"].append({"bookmaker": name, "odds": h2h[event["away_team"]]})

                over_key = "totals_over_2.5"
                under_key = "totals_under_2.5"
                if over_key in markets:
                    best["over_2_5"].append({"bookmaker": name, "odds": markets[over_key]})
                if under_key in markets:
                    best["under_2_5"].append({"bookmaker": name, "odds": markets[under_key]})

        # Trier et garder les top N pour chaque marché
        for key in best:
            best[key] = sorted(best[key], key=lambda x: x["odds"], reverse=True)[:top_n]

        return best

    def _generate_simulated_odds(self, home_team: str, away_team: str, top_n: int = 4) -> dict:
        """Génère des cotes simulées basées sur la force relative des équipes."""
        from ligue1_teams import LIGUE1_TEAMS, find_team_key

        home_key = find_team_key(home_team)
        away_key = find_team_key(away_team)

        # Calculer la force moyenne
        home_rating = 75
        away_rating = 75

        if home_key and home_key in LIGUE1_TEAMS:
            team = LIGUE1_TEAMS[home_key]
            all_players = []
            for pos_players in team["squad"].values():
                all_players.extend(pos_players)
            if all_players:
                home_rating = sum(p["rating"] for p in all_players) / len(all_players)

        if away_key and away_key in LIGUE1_TEAMS:
            team = LIGUE1_TEAMS[away_key]
            all_players = []
            for pos_players in team["squad"].values():
                all_players.extend(pos_players)
            if all_players:
                away_rating = sum(p["rating"] for p in all_players) / len(all_players)

        # Avantage domicile +3 rating
        home_rating += 3
        diff = home_rating - away_rating

        # Convertir en probabilités
        import math
        home_prob = 1 / (1 + math.exp(-diff / 5))
        draw_prob = 0.25 - abs(diff) * 0.008
        draw_prob = max(0.15, min(0.30, draw_prob))
        away_prob = 1 - home_prob - draw_prob

        # S'assurer que les probas sont valides
        total = home_prob + draw_prob + away_prob
        home_prob /= total
        draw_prob /= total
        away_prob /= total

        # Convertir en cotes (avec marge bookmaker ~5%)
        margin = 1.05
        home_odds = round(margin / home_prob, 2)
        draw_odds = round(margin / draw_prob, 2)
        away_odds = round(margin / away_prob, 2)

        bookmakers_data = [
            ("Bet365", 0), ("Betclic", 0.02), ("Winamax", -0.01), ("Unibet", 0.03),
            ("1xBet", -0.02), ("Bwin", 0.01), ("PMU", 0.04), ("ParionsSport", 0.02),
        ]

        best = {
            "home_win": [],
            "draw": [],
            "away_win": [],
            "over_2_5": [],
            "under_2_5": [],
        }

        import random
        random.seed(hash(f"{home_team}{away_team}"))

        for bm_name, offset in bookmakers_data:
            variation = random.uniform(-0.08, 0.08)
            best["home_win"].append({
                "bookmaker": bm_name,
                "odds": round(home_odds + offset + variation, 2)
            })
            best["draw"].append({
                "bookmaker": bm_name,
                "odds": round(draw_odds + offset + variation, 2)
            })
            best["away_win"].append({
                "bookmaker": bm_name,
                "odds": round(away_odds + offset + variation, 2)
            })

            over_odds = round(random.uniform(1.75, 2.10), 2)
            under_odds = round(random.uniform(1.65, 2.00), 2)
            best["over_2_5"].append({"bookmaker": bm_name, "odds": over_odds})
            best["under_2_5"].append({"bookmaker": bm_name, "odds": under_odds})

        # Trier et garder les top N
        for key in best:
            best[key] = sorted(best[key], key=lambda x: x["odds"], reverse=True)[:top_n]

        return best

    async def get_last_lineups(self, team_id: int, count: int = 3) -> list[dict]:
        """
        Récupère les vraies compositions des derniers matchs joués.
        C'est LA source la plus fiable pour prédire le prochain XI.
        """
        # D'abord récupérer les derniers matchs joués
        fixtures_data = await self._api_football_request("fixtures", {
            "league": LIGUE1_LEAGUE_ID,
            "season": CURRENT_SEASON,
            "team": team_id,
            "last": count,
        })

        if "error" in fixtures_data:
            return []

        lineups_list = []
        fixture_ids = [
            item["fixture"]["id"]
            for item in fixtures_data.get("response", [])
            if item.get("fixture", {}).get("id")
        ]

        # Récupérer les compositions de chaque match
        for fixture_id in fixture_ids:
            lineup_data = await self._api_football_request("fixtures/lineups", {
                "fixture": fixture_id,
            })

            if "error" in lineup_data:
                continue

            for team_lineup in lineup_data.get("response", []):
                if team_lineup.get("team", {}).get("id") == team_id:
                    coach = team_lineup.get("coach", {})
                    formation = team_lineup.get("formation", "4-3-3")
                    starters = []
                    subs = []

                    for player in team_lineup.get("startXI", []):
                        p = player.get("player", {})
                        starters.append({
                            "name": p.get("name", ""),
                            "number": p.get("number", 0),
                            "pos": p.get("pos", ""),  # G, D, M, F
                            "grid": p.get("grid", ""),
                        })

                    for player in team_lineup.get("substitutes", []):
                        p = player.get("player", {})
                        subs.append({
                            "name": p.get("name", ""),
                            "number": p.get("number", 0),
                            "pos": p.get("pos", ""),
                        })

                    lineups_list.append({
                        "fixture_id": fixture_id,
                        "coach": coach.get("name", ""),
                        "formation": formation,
                        "starters": starters,
                        "substitutes": subs,
                    })
                    break

        return lineups_list

    async def fetch_league_team_ids(self) -> dict[str, int]:
        """
        Récupère les vrais IDs des équipes Ligue 1 depuis l'API.
        Retourne un dict {nom_normalisé: team_id}.
        """
        data = await self._api_football_request("teams", {
            "league": LIGUE1_LEAGUE_ID,
            "season": CURRENT_SEASON,
        })

        if "error" in data or not data.get("response"):
            return {}

        team_ids = {}
        for entry in data["response"]:
            team = entry.get("team", {})
            name = team.get("name", "")
            tid = team.get("id")
            if name and tid:
                team_ids[name.lower()] = tid
        return team_ids

    async def _auto_fix_team_ids(self):
        """
        Récupère les IDs réels de l'API et met à jour LIGUE1_TEAMS en mémoire.
        Fait une correspondance par nom d'équipe (fuzzy matching basique).
        """
        from ligue1_teams import LIGUE1_TEAMS

        api_teams = await self.fetch_league_team_ids()
        if not api_teams:
            return

        # Correspondances manuelles: clé LIGUE1_TEAMS -> sous-chaîne dans le nom API
        name_map = {
            "psg": "paris saint",
            "om": "marseille",
            "monaco": "monaco",
            "lille": "lille",
            "lens": "lens",
            "ol": "lyon",
            "nice": "nice",
            "rennes": "rennes",
            "toulouse": "toulouse",
            "brest": "brest",
            "strasbourg": "strasbourg",
            "nantes": "nantes",
            "angers": "angers",
            "auxerre": "auxerre",
            "le_havre": "havre",
            "lorient": "lorient",
            "paris_fc": "paris fc",
            "metz": "metz",
            # Fallback pour futures promotions
            "montpellier": "montpellier",
            "saint_etienne": "saint-etienne",
            "reims": "reims",
        }

        for team_key, team_data in LIGUE1_TEAMS.items():
            search_term = name_map.get(team_key, team_key.replace("_", " "))
            for api_name, api_id in api_teams.items():
                if search_term in api_name:
                    old_id = team_data.get("api_football_id")
                    if old_id != api_id:
                        print(f"   🔄 {team_data.get('name', team_key)}: ID {old_id} → {api_id}")
                        team_data["api_football_id"] = api_id
                    break

    async def get_current_squad(self, team_id: int) -> list[dict]:
        """
        Récupère l'effectif actuel d'une équipe depuis API-Football.
        Inclut les joueurs avec leur poste et numéro.
        """
        data = await self._api_football_request("players/squads", {
            "team": team_id,
        })

        if "error" in data:
            return []

        squad = []
        for team_data in data.get("response", []):
            for player in team_data.get("players", []):
                squad.append({
                    "name": player.get("name", ""),
                    "age": player.get("age", 0),
                    "number": player.get("number", 0),
                    "position": player.get("position", ""),  # Goalkeeper, Defender, Midfielder, Attacker
                    "photo": player.get("photo", ""),
                })
        return squad

    async def get_coach(self, team_id: int) -> dict:
        """Récupère l'entraîneur actuel d'une équipe."""
        data = await self._api_football_request("coachs", {
            "team": team_id,
        })

        if "error" in data:
            return {}

        # Le dernier coach dans la liste est le coach actuel
        for coach in data.get("response", []):
            career = coach.get("career", [])
            for stint in career:
                if stint.get("team", {}).get("id") == team_id and stint.get("end") is None:
                    return {
                        "name": coach.get("name", ""),
                        "nationality": coach.get("nationality", ""),
                        "photo": coach.get("photo", ""),
                    }
        return {}

    def analyze_recent_lineups(self, lineups: list[dict]) -> dict:
        """
        Analyse les dernières compositions réelles pour identifier les titulaires réguliers.
        Retourne un XI probable basé sur la fréquence de titularisation.

        Args:
            lineups: Liste des compos des derniers matchs (de get_last_lineups)

        Returns:
            Dict avec formation probable, titulaires fréquents, coach
        """
        if not lineups:
            return {}

        # Compter les apparitions de chaque joueur comme titulaire
        player_counts = {}
        formation_counts = {}
        coach_name = lineups[0].get("coach", "")

        for lineup in lineups:
            formation = lineup.get("formation", "4-3-3")
            formation_counts[formation] = formation_counts.get(formation, 0) + 1

            for starter in lineup.get("starters", []):
                name = starter["name"]
                pos = starter.get("pos", "")
                if name not in player_counts:
                    player_counts[name] = {
                        "name": name,
                        "count": 0,
                        "pos": pos,
                        "number": starter.get("number", 0),
                    }
                player_counts[name]["count"] += 1

        # Formation la plus utilisée
        best_formation = max(formation_counts, key=formation_counts.get) if formation_counts else "4-3-3"

        # Trier les joueurs par fréquence de titularisation
        all_players = sorted(player_counts.values(), key=lambda x: x["count"], reverse=True)

        # Mapper les positions API-Football vers nos groupes
        pos_map = {"G": "GK", "D": "DEF", "M": "MID", "F": "FWD"}

        # Sélectionner le XI le plus probable
        probable_xi = []
        pos_limits = self._get_formation_limits(best_formation)

        filled = {"GK": 0, "DEF": 0, "MID": 0, "FWD": 0}
        for player in all_players:
            group = pos_map.get(player["pos"], "MID")
            if filled.get(group, 0) < pos_limits.get(group, 0):
                probable_xi.append({
                    "name": player["name"],
                    "number": player["number"],
                    "position_group": group,
                    "starts": player["count"],
                    "total_matches": len(lineups),
                })
                filled[group] = filled.get(group, 0) + 1

            if sum(filled.values()) >= 11:
                break

        return {
            "formation": best_formation,
            "coach": coach_name,
            "probable_xi": probable_xi,
            "total_matches_analyzed": len(lineups),
        }

    def _get_formation_limits(self, formation: str) -> dict:
        """Retourne les limites par poste pour une formation."""
        formations = {
            "4-3-3": {"GK": 1, "DEF": 4, "MID": 3, "FWD": 3},
            "4-4-2": {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2},
            "4-2-3-1": {"GK": 1, "DEF": 4, "MID": 5, "FWD": 1},
            "3-4-3": {"GK": 1, "DEF": 3, "MID": 4, "FWD": 3},
            "3-5-2": {"GK": 1, "DEF": 3, "MID": 5, "FWD": 2},
            "3-4-2-1": {"GK": 1, "DEF": 3, "MID": 6, "FWD": 1},
            "5-3-2": {"GK": 1, "DEF": 5, "MID": 3, "FWD": 2},
            "4-5-1": {"GK": 1, "DEF": 4, "MID": 5, "FWD": 1},
            "4-1-4-1": {"GK": 1, "DEF": 4, "MID": 5, "FWD": 1},
        }
        return formations.get(formation, {"GK": 1, "DEF": 4, "MID": 3, "FWD": 3})

    async def get_all_team_data_v2(self, team_id: int, team_name: str) -> dict:
        """
        Version améliorée : récupère TOUTES les données incluant les vraies compos.
        C'est cette méthode qui doit être appelée pour des prédictions fiables.
        """
        tasks = [
            self.get_injuries(team_id),
            self.get_team_stats(team_id),
            self.get_next_fixtures(team_id),
            self.get_last_results(team_id),
            self.get_last_lineups(team_id, count=5),
            self.get_current_squad(team_id),
            self.get_coach(team_id),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        lineups = results[4] if not isinstance(results[4], Exception) else []

        return {
            "injuries": results[0] if not isinstance(results[0], Exception) else [],
            "stats": results[1] if not isinstance(results[1], Exception) else {},
            "next_fixtures": results[2] if not isinstance(results[2], Exception) else [],
            "last_results": results[3] if not isinstance(results[3], Exception) else [],
            "last_lineups": lineups,
            "lineup_analysis": self.analyze_recent_lineups(lineups),
            "current_squad": results[5] if not isinstance(results[5], Exception) else [],
            "coach": results[6] if not isinstance(results[6], Exception) else {},
        }

    async def refresh_all_squads(self) -> int:
        """
        Met à jour les effectifs de TOUTES les équipes Ligue 1 en mémoire
        depuis API-Football. Appelé automatiquement au démarrage du bot.

        Modifie directement LIGUE1_TEAMS en mémoire (pas le fichier).
        Retourne le nombre d'équipes mises à jour.
        """
        from ligue1_teams import LIGUE1_TEAMS

        if not self.api_football_key:
            return 0

        # D'abord, corriger automatiquement les IDs depuis l'API
        await self._auto_fix_team_ids()

        updated = 0
        pos_map = {
            "Goalkeeper": "GK",
            "Defender": "DEF",
            "Midfielder": "MID",
            "Attacker": "FWD",
        }
        detail_pos = {
            "Goalkeeper": None,
            "Defender": "DC",
            "Midfielder": "MC",
            "Attacker": "BU",
        }

        for team_key, team_data in LIGUE1_TEAMS.items():
            team_id = team_data.get("api_football_id")
            if not team_id:
                continue

            try:
                # Récupérer effectif + coach en parallèle
                squad_raw, coach_data = await asyncio.gather(
                    self.get_current_squad(team_id),
                    self.get_coach(team_id),
                    return_exceptions=True,
                )

                if isinstance(squad_raw, Exception) or not squad_raw:
                    continue

                # Réorganiser par poste
                new_squad = {"GK": [], "DEF": [], "MID": [], "FWD": []}
                for player in squad_raw:
                    api_pos = player.get("position", "Midfielder")
                    group = pos_map.get(api_pos, "MID")
                    p = {
                        "name": player["name"],
                        "number": player.get("number", 0),
                        "rating": 75,
                        "age": player.get("age", 0),
                    }
                    if group != "GK":
                        p["position"] = detail_pos.get(api_pos, "MC")
                    new_squad[group].append(p)

                # Mettre à jour l'effectif en mémoire
                team_data["squad"] = new_squad

                # Mettre à jour le coach
                if not isinstance(coach_data, Exception) and coach_data:
                    coach_name = coach_data.get("name", "")
                    if coach_name:
                        team_data["coach"] = coach_name

                # Reconstruire le default_xi avec les nouveaux joueurs
                formation = team_data.get("preferred_formations", ["4-3-3"])[0]
                formation_limits = self._get_formation_limits(formation)
                xi = []
                for group in ["GK", "DEF", "MID", "FWD"]:
                    players = new_squad.get(group, [])
                    count = formation_limits.get(group, 0)
                    for p in players[:count]:
                        name = p["name"]
                        parts = name.split()
                        xi.append(parts[-1] if len(parts) > 1 else name)

                team_data["default_xi"] = {"formation": formation, "lineup": xi}
                updated += 1

            except Exception:
                continue

            # Petite pause pour le rate limit
            await asyncio.sleep(0.5)

        return updated

    async def scrape_injuries_free(self, team_name: str) -> list[dict]:
        """
        Scrape les blessures depuis des sources gratuites (sportsgambler, betinf).
        Fallback quand pas d'API key.
        """
        injuries = []
        url = "https://www.sportsgambler.com/injuries/football/france-ligue-1/"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        # Parsing basique - chercher le nom de l'équipe dans le HTML
                        if team_name.lower() in html.lower():
                            # Note: un vrai parser HTML serait mieux ici
                            # Pour l'instant on retourne les données simulées
                            pass
        except Exception:
            pass

        return injuries

    async def get_all_team_data(self, team_id: int, team_name: str) -> dict:
        """Récupère toutes les données d'une équipe en parallèle."""
        tasks = [
            self.get_injuries(team_id),
            self.get_team_stats(team_id),
            self.get_next_fixtures(team_id),
            self.get_last_results(team_id),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            "injuries": results[0] if not isinstance(results[0], Exception) else [],
            "stats": results[1] if not isinstance(results[1], Exception) else {},
            "next_fixtures": results[2] if not isinstance(results[2], Exception) else [],
            "last_results": results[3] if not isinstance(results[3], Exception) else [],
        }
