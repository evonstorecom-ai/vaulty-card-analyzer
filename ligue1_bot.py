#!/usr/bin/env python3
"""
Bot de Prédiction Ligue 1 2025-2026
====================================
Prédit les titularisations, résultats et cotes des matchs de Ligue 1.

Utilisation:
    python ligue1_bot.py                    # Mode interactif
    python ligue1_bot.py --team "Lyon"      # Analyse d'une équipe
    python ligue1_bot.py --match "PSG" "OM" # Analyse d'un match

Variables d'environnement:
    API_FOOTBALL_KEY  - Clé API-Football (optionnel, données simulées sinon)
    ODDS_API_KEY      - Clé The Odds API (optionnel, cotes simulées sinon)
"""

import asyncio
import argparse
import sys
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.layout import Layout
from rich.markdown import Markdown
from rich import box

from ligue1_teams import (
    LIGUE1_TEAMS, find_team, find_team_key, list_all_teams, TEAM_ALIASES
)
from ligue1_predictor import Ligue1Predictor
from ligue1_data_fetcher import Ligue1DataFetcher

console = Console()
predictor = Ligue1Predictor()
fetcher = Ligue1DataFetcher()


# ─────────────────────────────────────────────────────────
# AFFICHAGE RICH
# ─────────────────────────────────────────────────────────

def display_banner():
    """Affiche la bannière du bot."""
    banner = """
[bold cyan]╔══════════════════════════════════════════════════════════════╗
║          LIGUE 1 LINEUP PREDICTOR 2025-2026                 ║
║          Bot de Prédiction des Titularisations              ║
╚══════════════════════════════════════════════════════════════╝[/bold cyan]
    """
    console.print(banner)


def display_team_info(team: dict):
    """Affiche les informations d'une équipe."""
    info = Table(show_header=False, box=box.ROUNDED, border_style="cyan")
    info.add_column("Clé", style="bold white")
    info.add_column("Valeur", style="yellow")

    info.add_row("Club", team["full_name"])
    info.add_row("Coach", team["coach"])
    info.add_row("Stade", team["stadium"])
    info.add_row("Ville", team["city"])
    info.add_row("Style de jeu", team["style"])
    info.add_row("Formations", " / ".join(team["preferred_formations"]))

    console.print(Panel(info, title=f"[bold white]{team['full_name']}[/bold white]", border_style="cyan"))


def display_lineup(lineup_data: dict, side: str = ""):
    """Affiche le 11 de départ prédit."""
    if "error" in lineup_data:
        console.print(f"[red]Erreur: {lineup_data['error']}[/red]")
        return

    title_color = "green" if side == "home" else "red" if side == "away" else "cyan"
    side_label = " (DOM)" if side == "home" else " (EXT)" if side == "away" else ""

    # Formation et coach
    console.print(f"\n[bold {title_color}]{'━' * 50}[/bold {title_color}]")
    console.print(
        f"[bold {title_color}]{lineup_data['team_name']}{side_label}[/bold {title_color}]"
    )
    console.print(
        f"[dim]Coach: {lineup_data['coach']} | Formation: {lineup_data['formation']}[/dim]"
    )
    console.print(f"[dim]Style: {lineup_data['style']}[/dim]")

    # Tableau du 11 titulaire
    table = Table(
        title=f"XI DE DEPART - {lineup_data['formation']}",
        box=box.DOUBLE_EDGE,
        border_style=title_color,
        show_lines=True,
    )
    table.add_column("#", style="bold", width=4, justify="center")
    table.add_column("Joueur", style="bold white", min_width=22)
    table.add_column("Poste", style="cyan", width=6, justify="center")
    table.add_column("Rating", width=8, justify="center")

    for player in lineup_data["lineup"]:
        rating = player.get("rating", 0)
        if rating >= 85:
            rating_style = "[bold green]"
        elif rating >= 80:
            rating_style = "[green]"
        elif rating >= 75:
            rating_style = "[yellow]"
        else:
            rating_style = "[red]"

        pos = player.get("position", player.get("position_group", ""))
        table.add_row(
            str(player.get("number", "")),
            player["name"],
            pos,
            f"{rating_style}{rating}[/]",
        )

    console.print(table)

    # Remplaçants
    if lineup_data.get("bench"):
        bench_table = Table(
            title="BANC DES REMPLACANTS",
            box=box.SIMPLE,
            border_style="dim",
        )
        bench_table.add_column("#", width=4, justify="center")
        bench_table.add_column("Joueur", min_width=20)
        bench_table.add_column("Poste", width=6, justify="center")
        bench_table.add_column("Rating", width=8, justify="center")

        for player in lineup_data["bench"]:
            pos = player.get("position", player.get("position_group", ""))
            bench_table.add_row(
                str(player.get("number", "")),
                player["name"],
                pos,
                str(player.get("rating", "")),
            )
        console.print(bench_table)

    # Joueurs indisponibles
    injuries = lineup_data.get("unavailable_injuries", [])
    suspensions = lineup_data.get("unavailable_suspensions", [])
    if injuries or suspensions:
        console.print(f"\n[bold red]JOUEURS INDISPONIBLES:[/bold red]")
        for name in injuries:
            console.print(f"  [red]  Blessé: {name}[/red]")
        for name in suspensions:
            console.print(f"  [yellow]  Suspendu: {name}[/yellow]")


def display_prediction(prediction: dict):
    """Affiche les prédictions de résultat."""
    if "error" in prediction:
        console.print(f"[red]Erreur: {prediction['error']}[/red]")
        return

    prob = prediction["probabilities"]
    score = prediction["predicted_score"]
    likely = prediction["most_likely_score"]

    console.print(f"\n[bold white]{'═' * 60}[/bold white]")
    console.print("[bold white]        PREDICTIONS DU MATCH[/bold white]")
    console.print(f"[bold white]{'═' * 60}[/bold white]")

    # Score prédit
    console.print(
        f"\n  [bold cyan]Score prédit:[/bold cyan]  "
        f"[bold green]{prediction['home_team']}[/bold green] "
        f"[bold white]{likely[0][0]} - {likely[0][1]}[/bold white] "
        f"[bold red]{prediction['away_team']}[/bold red]"
        f"  [dim]({likely[1]}% de probabilité)[/dim]"
    )

    # Buts moyens attendus
    console.print(
        f"  [dim]Buts moyens attendus: {score['home']:.1f} - {score['away']:.1f}[/dim]"
    )

    # Tableau des probabilités
    prob_table = Table(box=box.ROUNDED, border_style="white", show_header=True)
    prob_table.add_column("Issue", style="bold", justify="center", width=20)
    prob_table.add_column("Probabilité", justify="center", width=15)
    prob_table.add_column("Cote estimée", justify="center", width=15)

    # Couleurs selon les probabilités
    for label, key, color in [
        (f"Victoire {prediction['home_team'][:15]}", "home_win", "green"),
        ("Match Nul", "draw", "yellow"),
        (f"Victoire {prediction['away_team'][:15]}", "away_win", "red"),
    ]:
        pct = prob[key]
        odds = round(100 / pct, 2) if pct > 0 else 99.99
        bar = "█" * int(pct / 3) + "░" * (33 - int(pct / 3))
        prob_table.add_row(
            f"[{color}]{label}[/{color}]",
            f"[bold {color}]{pct}%[/bold {color}]  {bar[:20]}",
            f"[{color}]{odds:.2f}[/{color}]",
        )

    console.print(prob_table)

    # Statistiques supplémentaires pour les parieurs
    stats_table = Table(
        title="STATISTIQUES PARIS",
        box=box.ROUNDED,
        border_style="magenta",
    )
    stats_table.add_column("Marché", style="bold white", width=25)
    stats_table.add_column("Probabilité", justify="center", width=15)
    stats_table.add_column("Recommandation", justify="center", width=20)

    btts = prediction.get("btts_prob", 50)
    over25 = prediction.get("over_2_5_prob", 50)
    over15 = prediction.get("over_1_5_prob", 50)

    stats_table.add_row(
        "Les 2 équipes marquent (BTTS)",
        f"[bold]{'Oui' if btts > 50 else 'Non'}[/bold] ({btts}%)",
        f"[green]{'RECOMMANDÉ' if btts > 55 else ''}[/green]" if btts > 55 else "[yellow]NEUTRE[/yellow]",
    )
    stats_table.add_row(
        "Plus de 2.5 buts",
        f"[bold]{over25}%[/bold]",
        f"[green]RECOMMANDÉ[/green]" if over25 > 55 else "[yellow]NEUTRE[/yellow]",
    )
    stats_table.add_row(
        "Plus de 1.5 buts",
        f"[bold]{over15}%[/bold]",
        f"[green]RECOMMANDÉ[/green]" if over15 > 55 else "[yellow]NEUTRE[/yellow]",
    )
    stats_table.add_row(
        "Confiance prédiction",
        f"[bold]{prediction.get('confidence', 'N/A')}[/bold]",
        "",
    )

    console.print(stats_table)

    # Top scores les plus probables
    if prediction.get("top_scores"):
        console.print("\n[bold white]  Top 5 scores les plus probables:[/bold white]")
        for i, (score_tuple, prob_pct) in enumerate(prediction["top_scores"][:5], 1):
            bar = "█" * int(prob_pct)
            console.print(
                f"    {i}. [bold]{score_tuple[0]}-{score_tuple[1]}[/bold]  "
                f"[cyan]{prob_pct}%[/cyan]  {bar}"
            )


def display_odds(odds_data: dict, home_team: str, away_team: str):
    """Affiche les meilleures cotes des bookmakers."""
    if not odds_data:
        console.print("[yellow]Aucune cote disponible.[/yellow]")
        return

    console.print(f"\n[bold white]{'═' * 60}[/bold white]")
    console.print("[bold white]    MEILLEURES COTES - TOP 4 BOOKMAKERS[/bold white]")
    console.print(f"[bold white]{'═' * 60}[/bold white]")

    markets = [
        ("home_win", f"Victoire {home_team}", "green"),
        ("draw", "Match Nul", "yellow"),
        ("away_win", f"Victoire {away_team}", "red"),
        ("over_2_5", "Plus de 2.5 buts", "cyan"),
        ("under_2_5", "Moins de 2.5 buts", "magenta"),
    ]

    for market_key, market_name, color in markets:
        if market_key in odds_data and odds_data[market_key]:
            console.print(f"\n  [bold {color}]{market_name}:[/bold {color}]")
            odds_table = Table(box=box.SIMPLE, show_header=True, border_style=color)
            odds_table.add_column("Rang", width=5, justify="center")
            odds_table.add_column("Bookmaker", min_width=15)
            odds_table.add_column("Cote", width=8, justify="center", style="bold")
            odds_table.add_column("Lien", min_width=25)

            bookmaker_links = {
                "Bet365": "https://www.bet365.com",
                "Betclic": "https://www.betclic.fr",
                "Winamax": "https://www.winamax.fr",
                "Unibet": "https://www.unibet.fr",
                "1xBet": "https://1xbet.com",
                "Bwin": "https://www.bwin.fr",
                "PMU": "https://paris-sportifs.pmu.fr",
                "ParionsSport": "https://www.enligne.parionssport.fdj.fr",
                "Betway": "https://www.betway.com",
                "Pinnacle": "https://www.pinnacle.com",
                "William Hill": "https://www.williamhill.com",
            }

            for i, odd in enumerate(odds_data[market_key][:4], 1):
                bm = odd["bookmaker"]
                link = bookmaker_links.get(bm, f"https://www.google.com/search?q={bm}+paris+sportifs")
                odds_table.add_row(
                    f"#{i}",
                    bm,
                    f"[bold {color}]{odd['odds']:.2f}[/bold {color}]",
                    f"[link={link}]{link}[/link]",
                )

            console.print(odds_table)


def display_all_teams():
    """Affiche la liste de toutes les équipes."""
    table = Table(
        title="EQUIPES LIGUE 1 2025-2026",
        box=box.DOUBLE_EDGE,
        border_style="cyan",
    )
    table.add_column("#", width=4, justify="center", style="bold")
    table.add_column("Club", min_width=25, style="bold white")
    table.add_column("Coach", min_width=20)
    table.add_column("Stade", min_width=20)
    table.add_column("Alias", min_width=15, style="dim")

    for i, (key, team) in enumerate(LIGUE1_TEAMS.items(), 1):
        table.add_row(
            str(i),
            team["full_name"],
            team["coach"],
            team["stadium"],
            key.upper(),
        )

    console.print(table)


# ─────────────────────────────────────────────────────────
# COMMANDES PRINCIPALES
# ─────────────────────────────────────────────────────────

async def analyze_team(team_query: str):
    """Analyse complète d'une équipe: composition prédite + prochains matchs."""
    team = find_team(team_query)
    team_key = find_team_key(team_query)

    if not team:
        console.print(f"[red]Équipe '{team_query}' non trouvée.[/red]")
        console.print("[yellow]Équipes disponibles:[/yellow]")
        display_all_teams()
        return

    display_team_info(team)

    # Essayer de récupérer les données en temps réel
    console.print("\n[dim]Récupération des données en temps réel...[/dim]")

    team_id = team.get("api_football_id", 0)
    live_data = await fetcher.get_all_team_data(team_id, team["full_name"])

    injuries = []
    suspensions = []

    # Extraire les blessures des données live
    for inj in live_data.get("injuries", []):
        reason = inj.get("reason", "").lower()
        if "suspended" in reason or "suspen" in reason or "card" in reason:
            suspensions.append(inj["player_name"])
        else:
            injuries.append(inj["player_name"])

    # Forme récente
    form = ""
    stats = live_data.get("stats", {})
    if stats:
        form = stats.get("form", "")

    # Si pas de données live, afficher un message
    if not injuries and not suspensions:
        console.print(
            "[yellow]Pas de données live disponibles (configurez API_FOOTBALL_KEY).[/yellow]"
        )
        console.print("[yellow]Utilisation des données de base pour la prédiction.[/yellow]")

    # Prédire la composition
    lineup = predictor.predict_lineup(team_key, injuries, suspensions)
    display_lineup(lineup)

    # Prochains matchs
    fixtures = live_data.get("next_fixtures", [])
    if fixtures:
        console.print(f"\n[bold white]PROCHAINS MATCHS:[/bold white]")
        for fx in fixtures:
            console.print(
                f"  {fx['date'][:10]}  "
                f"[green]{fx['home_team']}[/green] vs "
                f"[red]{fx['away_team']}[/red]  "
                f"[dim]{fx['venue']}[/dim]"
            )

    # Derniers résultats
    results = live_data.get("last_results", [])
    if results:
        console.print(f"\n[bold white]DERNIERS RESULTATS:[/bold white]")
        for res in results:
            home = res["home_team"]
            away = res["away_team"]
            hg = res["home_goals"]
            ag = res["away_goals"]
            date = res["date"][:10] if res["date"] else ""
            console.print(f"  {date}  {home} {hg}-{ag} {away}")


async def analyze_match(home_query: str, away_query: str):
    """Analyse complète d'un match: compositions, prédictions, cotes."""
    home_key = find_team_key(home_query)
    away_key = find_team_key(away_query)

    if not home_key or home_key not in LIGUE1_TEAMS:
        console.print(f"[red]Équipe domicile '{home_query}' non trouvée.[/red]")
        display_all_teams()
        return

    if not away_key or away_key not in LIGUE1_TEAMS:
        console.print(f"[red]Équipe extérieur '{away_query}' non trouvée.[/red]")
        display_all_teams()
        return

    home_team = LIGUE1_TEAMS[home_key]
    away_team = LIGUE1_TEAMS[away_key]

    # En-tête du match
    console.print(f"\n[bold white]{'═' * 60}[/bold white]")
    console.print(
        f"[bold green]  {home_team['full_name']}[/bold green]"
        f"  [bold white]vs[/bold white]  "
        f"[bold red]{away_team['full_name']}[/bold red]"
    )
    console.print(f"  [dim]{home_team['stadium']} - {home_team['city']}[/dim]")
    console.print(f"[bold white]{'═' * 60}[/bold white]")

    # Récupérer les données en temps réel pour les deux équipes
    console.print("\n[dim]Récupération des données...[/dim]")

    home_data, away_data = await asyncio.gather(
        fetcher.get_all_team_data(home_team["api_football_id"], home_team["full_name"]),
        fetcher.get_all_team_data(away_team["api_football_id"], away_team["full_name"]),
    )

    # Extraire blessures
    home_injuries, home_suspensions = _extract_unavailable(home_data)
    away_injuries, away_suspensions = _extract_unavailable(away_data)

    # Formes
    home_form = home_data.get("stats", {}).get("form", "")
    away_form = away_data.get("stats", {}).get("form", "")

    # Analyse complète
    analysis = predictor.generate_match_analysis(
        home_key, away_key,
        home_injuries, away_injuries,
        home_suspensions, away_suspensions,
        home_form, away_form,
    )

    # Afficher les compositions
    display_lineup(analysis["home_lineup"], side="home")
    display_lineup(analysis["away_lineup"], side="away")

    # Afficher les prédictions
    display_prediction(analysis["prediction"])

    # Récupérer et afficher les cotes
    console.print("\n[dim]Récupération des cotes...[/dim]")
    odds = await fetcher.get_best_odds(home_team["full_name"], away_team["full_name"])
    display_odds(odds, home_team["short_name"], away_team["short_name"])

    # Conseil final
    pred = analysis["prediction"]
    console.print(f"\n[bold white]{'═' * 60}[/bold white]")
    console.print("[bold cyan]  CONSEIL DU BOT:[/bold cyan]")

    prob = pred["probabilities"]
    if prob["home_win"] > 55:
        console.print(
            f"  [green]Victoire probable de {pred['home_team']} "
            f"({prob['home_win']}%)[/green]"
        )
    elif prob["away_win"] > 55:
        console.print(
            f"  [red]Victoire probable de {pred['away_team']} "
            f"({prob['away_win']}%)[/red]"
        )
    else:
        console.print(
            f"  [yellow]Match équilibré - Nul possible ({prob['draw']}%)[/yellow]"
        )

    btts = pred.get("btts_prob", 0)
    over25 = pred.get("over_2_5_prob", 0)
    if btts > 55:
        console.print(f"  [cyan]BTTS recommandé ({btts}%)[/cyan]")
    if over25 > 55:
        console.print(f"  [cyan]Over 2.5 recommandé ({over25}%)[/cyan]")

    console.print(f"\n  [dim]Confiance: {pred.get('confidence', 'N/A')}[/dim]")
    console.print(
        f"  [dim]Disclaimer: Les prédictions sont à titre indicatif. "
        f"Pariez de manière responsable.[/dim]"
    )


def _extract_unavailable(data: dict) -> tuple[list, list]:
    """Extrait les blessés et suspendus des données."""
    injuries = []
    suspensions = []
    for inj in data.get("injuries", []):
        reason = inj.get("reason", "").lower()
        if "suspended" in reason or "card" in reason:
            suspensions.append(inj["player_name"])
        else:
            injuries.append(inj["player_name"])
    return injuries, suspensions


# ─────────────────────────────────────────────────────────
# MODE INTERACTIF
# ─────────────────────────────────────────────────────────

async def interactive_mode():
    """Mode interactif du bot."""
    display_banner()

    console.print("[bold white]Commandes disponibles:[/bold white]")
    console.print("  [cyan]equipe <nom>[/cyan]     - Analyse d'une équipe (ex: equipe Lyon)")
    console.print("  [cyan]match <dom> <ext>[/cyan] - Analyse d'un match (ex: match PSG OM)")
    console.print("  [cyan]liste[/cyan]             - Liste des équipes")
    console.print("  [cyan]aide[/cyan]              - Aide")
    console.print("  [cyan]quitter[/cyan]           - Quitter")
    console.print()

    while True:
        try:
            user_input = console.input("[bold cyan]Ligue1Bot > [/bold cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]Au revoir![/yellow]")
            break

        if not user_input:
            continue

        parts = user_input.lower().split(maxsplit=2)
        command = parts[0]

        if command in ("quitter", "quit", "exit", "q"):
            console.print("[yellow]Au revoir![/yellow]")
            break

        elif command in ("liste", "list", "equipes", "teams"):
            display_all_teams()

        elif command in ("equipe", "team", "analyse"):
            if len(parts) < 2:
                console.print("[red]Usage: equipe <nom de l'équipe>[/red]")
                continue
            team_name = " ".join(parts[1:])
            await analyze_team(team_name)

        elif command in ("match", "vs", "game"):
            if len(parts) < 3:
                console.print("[red]Usage: match <équipe domicile> <équipe extérieur>[/red]")
                console.print("[dim]Exemple: match PSG OM[/dim]")
                continue
            home = parts[1]
            away = parts[2]
            await analyze_match(home, away)

        elif command in ("aide", "help", "?"):
            console.print("\n[bold white]AIDE - Bot Ligue 1 Predictor[/bold white]")
            console.print("─" * 40)
            console.print("[cyan]equipe <nom>[/cyan]")
            console.print("  Affiche l'analyse complète d'une équipe:")
            console.print("  - Effectif et ratings des joueurs")
            console.print("  - XI de départ prédit")
            console.print("  - Blessés et suspendus (si API configurée)")
            console.print("  - Prochains matchs et derniers résultats")
            console.print()
            console.print("[cyan]match <domicile> <extérieur>[/cyan]")
            console.print("  Analyse complète d'un match:")
            console.print("  - XI de départ prédit pour les 2 équipes")
            console.print("  - Prédiction de résultat et score")
            console.print("  - Probabilités (1X2, BTTS, Over/Under)")
            console.print("  - Top 4 meilleures cotes par bookmaker")
            console.print("  - Liens vers les bookmakers")
            console.print()
            console.print("[dim]Alias acceptés: Lyon/OL, Marseille/OM, Paris/PSG, etc.[/dim]")
            console.print()
            console.print("[dim]Variables d'environnement pour les données live:[/dim]")
            console.print("[dim]  API_FOOTBALL_KEY - depuis api-football.com (gratuit)[/dim]")
            console.print("[dim]  ODDS_API_KEY     - depuis the-odds-api.com (gratuit)[/dim]")

        else:
            # Essayer de deviner si c'est un nom d'équipe
            team = find_team(user_input)
            if team:
                await analyze_team(user_input)
            else:
                console.print(
                    f"[red]Commande inconnue: '{command}'[/red]"
                )
                console.print("[dim]Tapez 'aide' pour voir les commandes disponibles.[/dim]")


# ─────────────────────────────────────────────────────────
# POINT D'ENTREE
# ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Bot de Prédiction Ligue 1 2025-2026"
    )
    parser.add_argument(
        "--team", "-t",
        help="Nom de l'équipe à analyser (ex: Lyon, PSG, Marseille)"
    )
    parser.add_argument(
        "--match", "-m",
        nargs=2,
        metavar=("DOMICILE", "EXTERIEUR"),
        help="Analyser un match (ex: --match PSG OM)"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="Afficher la liste des équipes"
    )

    args = parser.parse_args()

    if args.list:
        display_banner()
        display_all_teams()
    elif args.team:
        display_banner()
        asyncio.run(analyze_team(args.team))
    elif args.match:
        display_banner()
        asyncio.run(analyze_match(args.match[0], args.match[1]))
    else:
        asyncio.run(interactive_mode())


if __name__ == "__main__":
    main()
