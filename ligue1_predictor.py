"""
Moteur de prédiction Ligue 1.
Prédit les compositions d'équipe, les résultats et les scores.
"""

import math
import random
from datetime import datetime
from ligue1_teams import LIGUE1_TEAMS, find_team, find_team_key


class Ligue1Predictor:
    """Moteur de prédiction pour les matchs de Ligue 1."""

    # Pondération des facteurs de prédiction
    WEIGHTS = {
        "rating": 0.35,
        "form": 0.25,
        "home_advantage": 0.15,
        "injuries": 0.15,
        "h2h": 0.10,
    }

    def __init__(self):
        pass

    def predict_lineup(
        self,
        team_key: str,
        injuries: list[str] = None,
        suspensions: list[str] = None,
        preferred_formation: str = None,
    ) -> dict:
        """
        Prédit le 11 de départ d'une équipe.

        Args:
            team_key: Clé de l'équipe dans LIGUE1_TEAMS
            injuries: Liste des noms de joueurs blessés
            suspensions: Liste des noms de joueurs suspendus
            preferred_formation: Formation à utiliser (sinon celle par défaut)

        Returns:
            Dict avec la formation, le 11 titulaire et les remplaçants
        """
        if team_key not in LIGUE1_TEAMS:
            return {"error": f"Équipe '{team_key}' non trouvée"}

        team = LIGUE1_TEAMS[team_key]
        injuries = injuries or []
        suspensions = suspensions or []
        unavailable = set(name.lower() for name in injuries + suspensions)

        formation = preferred_formation or team["default_xi"]["formation"]

        # Positions requises selon la formation
        formation_slots = self._get_formation_slots(formation)

        # Sélectionner les joueurs disponibles par poste
        squad = team["squad"]
        available = {}
        for pos_group, players in squad.items():
            available[pos_group] = [
                p for p in players
                if p["name"].lower() not in unavailable
            ]

        # Construire le 11
        lineup = self._select_best_xi(available, formation_slots, team["default_xi"]["lineup"], unavailable)

        # Remplaçants
        starters_names = set(p["name"] for p in lineup)
        bench = []
        for pos_group, players in squad.items():
            for p in players:
                if p["name"] not in starters_names and p["name"].lower() not in unavailable:
                    bench.append(p)
        bench = sorted(bench, key=lambda x: x["rating"], reverse=True)[:7]

        return {
            "formation": formation,
            "coach": team["coach"],
            "team_name": team["full_name"],
            "style": team["style"],
            "lineup": lineup,
            "bench": bench,
            "unavailable_injuries": injuries,
            "unavailable_suspensions": suspensions,
        }

    def _get_formation_slots(self, formation: str) -> dict:
        """Retourne le nombre de joueurs par poste pour une formation."""
        formations = {
            "4-3-3": {"GK": 1, "DEF": 4, "MID": 3, "FWD": 3},
            "4-4-2": {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2},
            "4-2-3-1": {"GK": 1, "DEF": 4, "MID": 5, "FWD": 1},
            "3-4-3": {"GK": 1, "DEF": 3, "MID": 4, "FWD": 3},
            "3-5-2": {"GK": 1, "DEF": 3, "MID": 5, "FWD": 2},
            "3-4-2-1": {"GK": 1, "DEF": 3, "MID": 6, "FWD": 1},
            "3-4-1-2": {"GK": 1, "DEF": 3, "MID": 5, "FWD": 2},
            "4-1-4-1": {"GK": 1, "DEF": 4, "MID": 5, "FWD": 1},
            "5-3-2": {"GK": 1, "DEF": 5, "MID": 3, "FWD": 2},
            "4-5-1": {"GK": 1, "DEF": 4, "MID": 5, "FWD": 1},
        }
        return formations.get(formation, {"GK": 1, "DEF": 4, "MID": 3, "FWD": 3})

    def _select_best_xi(
        self,
        available: dict,
        slots: dict,
        default_lineup: list[str],
        unavailable: set,
    ) -> list[dict]:
        """Sélectionne le meilleur 11 en priorisant les titulaires habituels."""
        selected = []
        default_lower = set(n.lower() for n in default_lineup)

        for pos_group, count in slots.items():
            players = available.get(pos_group, [])

            # Prioriser les joueurs du 11 type
            default_players = [p for p in players if p["name"].lower() in default_lower]
            other_players = [p for p in players if p["name"].lower() not in default_lower]
            other_players.sort(key=lambda x: x["rating"], reverse=True)

            ordered = default_players + other_players

            for p in ordered[:count]:
                player_info = dict(p)
                player_info["position_group"] = pos_group
                selected.append(player_info)

        return selected

    def predict_match_result(
        self,
        home_team_key: str,
        away_team_key: str,
        home_injuries: list[str] = None,
        away_injuries: list[str] = None,
        home_form: str = "",
        away_form: str = "",
    ) -> dict:
        """
        Prédit le résultat d'un match.

        Returns:
            Dict avec les probabilités de victoire, nul, défaite et score prédit.
        """
        home_team = LIGUE1_TEAMS.get(home_team_key)
        away_team = LIGUE1_TEAMS.get(away_team_key)

        if not home_team or not away_team:
            return {"error": "Équipe(s) non trouvée(s)"}

        home_injuries = home_injuries or []
        away_injuries = away_injuries or []

        # 1. Force de l'effectif (rating moyen)
        home_rating = self._calc_squad_rating(home_team, home_injuries)
        away_rating = self._calc_squad_rating(away_team, away_injuries)

        # 2. Forme récente
        home_form_score = self._calc_form_score(home_form)
        away_form_score = self._calc_form_score(away_form)

        # 3. Avantage domicile
        home_advantage = 5.0  # Points de rating bonus pour l'équipe à domicile

        # 4. Impact des blessures
        home_injury_impact = len(home_injuries) * -1.5
        away_injury_impact = len(away_injuries) * -1.5

        # Score composite
        home_score = (
            home_rating * self.WEIGHTS["rating"]
            + home_form_score * self.WEIGHTS["form"]
            + home_advantage * self.WEIGHTS["home_advantage"]
            + home_injury_impact * self.WEIGHTS["injuries"]
        )

        away_score = (
            away_rating * self.WEIGHTS["rating"]
            + away_form_score * self.WEIGHTS["form"]
            + away_injury_impact * self.WEIGHTS["injuries"]
        )

        # Différence de force
        diff = home_score - away_score

        # Convertir en probabilités via logistique
        home_win_prob = 1 / (1 + math.exp(-diff / 4))
        draw_base = 0.26
        draw_prob = draw_base - abs(diff) * 0.012
        draw_prob = max(0.12, min(0.32, draw_prob))

        away_win_prob = 1 - home_win_prob - draw_prob

        # Normaliser
        total = home_win_prob + draw_prob + away_win_prob
        home_win_prob /= total
        draw_prob /= total
        away_win_prob /= total

        # Prédiction de score
        avg_goals_home = self._predict_goals(home_rating, away_rating, is_home=True)
        avg_goals_away = self._predict_goals(away_rating, home_rating, is_home=False)

        # Score le plus probable
        scores = self._most_likely_scores(avg_goals_home, avg_goals_away)

        return {
            "home_team": home_team["full_name"],
            "away_team": away_team["full_name"],
            "probabilities": {
                "home_win": round(home_win_prob * 100, 1),
                "draw": round(draw_prob * 100, 1),
                "away_win": round(away_win_prob * 100, 1),
            },
            "predicted_score": {
                "home": round(avg_goals_home, 1),
                "away": round(avg_goals_away, 1),
            },
            "most_likely_score": scores[0] if scores else (1, 1),
            "top_scores": scores[:5],
            "confidence": self._calc_confidence(diff),
            "btts_prob": round(self._calc_btts_probability(avg_goals_home, avg_goals_away) * 100, 1),
            "over_2_5_prob": round(self._calc_over_probability(avg_goals_home, avg_goals_away, 2.5) * 100, 1),
            "over_1_5_prob": round(self._calc_over_probability(avg_goals_home, avg_goals_away, 1.5) * 100, 1),
        }

    def _calc_squad_rating(self, team: dict, injuries: list[str]) -> float:
        """Calcule le rating moyen de l'effectif en excluant les blessés."""
        unavailable = set(name.lower() for name in injuries)
        all_players = []
        for players in team["squad"].values():
            all_players.extend(players)

        available = [p for p in all_players if p["name"].lower() not in unavailable]
        if not available:
            return 70.0

        # Pondérer les meilleurs joueurs (titulaires probables)
        available.sort(key=lambda x: x["rating"], reverse=True)
        top_11 = available[:11]
        return sum(p["rating"] for p in top_11) / len(top_11)

    def _calc_form_score(self, form: str) -> float:
        """Calcule un score de forme à partir de la chaîne WDLWW."""
        if not form:
            return 50.0

        points = {"W": 3, "D": 1, "L": 0}
        recent = form[-5:]  # 5 derniers matchs
        total = sum(points.get(c.upper(), 0) for c in recent)
        max_points = len(recent) * 3
        return (total / max_points) * 100 if max_points > 0 else 50.0

    def _predict_goals(self, attack_rating: float, defense_rating: float, is_home: bool) -> float:
        """Prédit le nombre moyen de buts."""
        base = 1.25  # Moyenne Ligue 1
        attack_factor = (attack_rating - 75) / 20
        defense_factor = (75 - defense_rating) / 25
        home_factor = 0.25 if is_home else 0.0

        goals = base + attack_factor + defense_factor + home_factor
        return max(0.3, min(3.5, goals))

    def _most_likely_scores(self, avg_home: float, avg_away: float) -> list[tuple]:
        """Retourne les scores les plus probables."""
        scores = []
        for h in range(6):
            for a in range(6):
                prob_h = (avg_home ** h) * math.exp(-avg_home) / math.factorial(h)
                prob_a = (avg_away ** a) * math.exp(-avg_away) / math.factorial(a)
                prob = prob_h * prob_a
                scores.append(((h, a), round(prob * 100, 1)))

        scores.sort(key=lambda x: x[1], reverse=True)
        return [(s[0], s[1]) for s in scores]

    def _calc_confidence(self, diff: float) -> str:
        """Calcule le niveau de confiance de la prédiction."""
        abs_diff = abs(diff)
        if abs_diff > 6:
            return "HAUTE"
        elif abs_diff > 3:
            return "MOYENNE"
        else:
            return "FAIBLE"

    def _calc_btts_probability(self, avg_home: float, avg_away: float) -> float:
        """Calcule la probabilité que les deux équipes marquent."""
        prob_home_scores = 1 - math.exp(-avg_home)
        prob_away_scores = 1 - math.exp(-avg_away)
        return prob_home_scores * prob_away_scores

    def _calc_over_probability(self, avg_home: float, avg_away: float, threshold: float) -> float:
        """Calcule la probabilité de plus de X buts."""
        avg_total = avg_home + avg_away
        # Utiliser la distribution de Poisson
        prob_under = 0
        for k in range(int(threshold) + 1):
            prob_under += (avg_total ** k) * math.exp(-avg_total) / math.factorial(k)
        return 1 - prob_under

    def generate_match_analysis(
        self,
        home_key: str,
        away_key: str,
        home_injuries: list[str] = None,
        away_injuries: list[str] = None,
        home_suspensions: list[str] = None,
        away_suspensions: list[str] = None,
        home_form: str = "",
        away_form: str = "",
    ) -> dict:
        """
        Génère une analyse complète d'un match avec compositions et prédictions.
        """
        home_unavailable = (home_injuries or []) + (home_suspensions or [])
        away_unavailable = (away_injuries or []) + (away_suspensions or [])

        # Prédire les compositions
        home_lineup = self.predict_lineup(home_key, home_injuries, home_suspensions)
        away_lineup = self.predict_lineup(away_key, away_injuries, away_suspensions)

        # Prédire le résultat
        result = self.predict_match_result(
            home_key, away_key,
            home_unavailable, away_unavailable,
            home_form, away_form,
        )

        return {
            "home_lineup": home_lineup,
            "away_lineup": away_lineup,
            "prediction": result,
        }
