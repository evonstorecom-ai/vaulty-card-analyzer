#!/usr/bin/env python3
"""
Bot Telegram - Ligue 1 Lineup Predictor 2025-2026
===================================================
Prédit les titularisations, résultats et cotes des matchs de Ligue 1
avec liens d'affiliation bookmakers intégrés.

Variables d'environnement requises:
    TELEGRAM_BOT_TOKEN   - Token du bot Telegram (via @BotFather)

Variables optionnelles pour les données live:
    API_FOOTBALL_KEY     - Clé API-Football (gratuit: api-football.com)
    ODDS_API_KEY         - Clé The Odds API (gratuit: the-odds-api.com)

Variables optionnelles pour l'affiliation (voir ligue1_affiliate.py):
    BETCLIC_AFFILIATE_ID, WINAMAX_AFFILIATE_ID, UNIBET_AFFILIATE_ID,
    ONEXBET_AFFILIATE_ID, PMU_AFFILIATE_ID, PARIONSSPORT_AFFILIATE_ID,
    BWIN_AFFILIATE_ID, ZEBET_AFFILIATE_ID
"""

import os
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Charger .env si présent
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if value and value not in ("", "votre_token_ici"):
                os.environ.setdefault(key, value)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode

from ligue1_teams import LIGUE1_TEAMS, find_team, find_team_key, list_all_teams
from ligue1_predictor import Ligue1Predictor
from ligue1_data_fetcher import Ligue1DataFetcher
from ligue1_affiliate import (
    get_affiliate_link,
    get_bookmaker_info,
    get_featured_platforms,
    format_featured_banner,
    format_odds_message_telegram,
    format_quick_odds_buttons,
    BOOKMAKER_CONFIG,
    FEATURED_PLATFORMS,
)

# Configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

predictor = Ligue1Predictor()
fetcher = Ligue1DataFetcher()


# ─────────────────────────────────────────────────────────
# HELPERS - FORMATAGE TELEGRAM
# ─────────────────────────────────────────────────────────

def format_lineup_telegram(lineup_data: dict, side: str = "") -> str:
    """Formate le 11 de départ pour Telegram (HTML)."""
    if "error" in lineup_data:
        return f"❌ Erreur: {lineup_data['error']}"

    side_emoji = "🏠" if side == "home" else "✈️" if side == "away" else "⚽"
    side_label = " (DOM)" if side == "home" else " (EXT)" if side == "away" else ""

    lines = []
    lines.append(f"{side_emoji} <b>{lineup_data['team_name']}{side_label}</b>")
    lines.append(f"👔 Coach: {lineup_data['coach']}")
    lines.append(f"📐 Formation: <b>{lineup_data['formation']}</b>")
    lines.append(f"🎯 Style: <i>{lineup_data['style']}</i>")
    lines.append("")
    lines.append(f"<b>📋 XI DE DÉPART ({lineup_data['formation']})</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━")

    # Grouper par poste
    position_emojis = {"GK": "🧤", "DEF": "🛡", "MID": "🎯", "FWD": "⚡"}
    current_group = ""

    for player in lineup_data["lineup"]:
        group = player.get("position_group", "")
        if group != current_group:
            current_group = group
            emoji = position_emojis.get(group, "⚽")
            lines.append(f"\n{emoji} <b>{group}</b>")

        rating = player.get("rating", 0)
        stars = "⭐" if rating >= 85 else "🌟" if rating >= 80 else ""
        pos = player.get("position", "")
        lines.append(
            f"  #{player.get('number', '?')} <b>{player['name']}</b> "
            f"({pos}) [{rating}] {stars}"
        )

    # Remplaçants
    if lineup_data.get("bench"):
        lines.append(f"\n🪑 <b>BANC:</b>")
        bench_names = [
            f"{p['name']} [{p.get('rating', '?')}]"
            for p in lineup_data["bench"]
        ]
        lines.append("  " + " • ".join(bench_names))

    # Indisponibles
    injuries = lineup_data.get("unavailable_injuries", [])
    suspensions = lineup_data.get("unavailable_suspensions", [])
    if injuries or suspensions:
        lines.append(f"\n🚑 <b>INDISPONIBLES:</b>")
        for name in injuries:
            lines.append(f"  🤕 {name} (blessé)")
        for name in suspensions:
            lines.append(f"  🟥 {name} (suspendu)")

    return "\n".join(lines)


def format_prediction_telegram(prediction: dict) -> str:
    """Formate les prédictions pour Telegram (HTML)."""
    if "error" in prediction:
        return f"❌ Erreur: {prediction['error']}"

    prob = prediction["probabilities"]
    score = prediction["predicted_score"]
    likely = prediction["most_likely_score"]

    lines = []
    lines.append("🔮 <b>PRÉDICTIONS</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")

    # Score prédit
    lines.append(
        f"📊 <b>Score prédit:</b> "
        f"{prediction['home_team']} <b>{likely[0][0]} - {likely[0][1]}</b> "
        f"{prediction['away_team']}"
    )
    lines.append(f"   <i>({likely[1]}% de probabilité)</i>")
    lines.append(f"   Buts moyens: {score['home']:.1f} - {score['away']:.1f}")
    lines.append("")

    # Probabilités 1X2
    lines.append("<b>📈 PROBABILITÉS:</b>")

    # Barres de progression
    def make_bar(pct):
        filled = int(pct / 5)
        return "▓" * filled + "░" * (20 - filled)

    lines.append(
        f"  🏠 Victoire {prediction['home_team'][:12]}: "
        f"<b>{prob['home_win']}%</b> {make_bar(prob['home_win'])}"
    )
    lines.append(
        f"  🤝 Match Nul: "
        f"<b>{prob['draw']}%</b> {make_bar(prob['draw'])}"
    )
    lines.append(
        f"  ✈️ Victoire {prediction['away_team'][:12]}: "
        f"<b>{prob['away_win']}%</b> {make_bar(prob['away_win'])}"
    )
    lines.append("")

    # Stats pour parieurs
    lines.append("<b>🎲 STATS PARIS:</b>")

    btts = prediction.get("btts_prob", 50)
    over25 = prediction.get("over_2_5_prob", 50)
    over15 = prediction.get("over_1_5_prob", 50)

    btts_icon = "✅" if btts > 55 else "⚠️" if btts > 45 else "❌"
    over25_icon = "✅" if over25 > 55 else "⚠️" if over25 > 45 else "❌"
    over15_icon = "✅" if over15 > 55 else "⚠️" if over15 > 45 else "❌"

    lines.append(f"  {btts_icon} BTTS (2 éq. marquent): <b>{btts}%</b>")
    lines.append(f"  {over25_icon} Over 2.5 buts: <b>{over25}%</b>")
    lines.append(f"  {over15_icon} Over 1.5 buts: <b>{over15}%</b>")
    lines.append(f"  📊 Confiance: <b>{prediction.get('confidence', 'N/A')}</b>")
    lines.append("")

    # Top scores
    lines.append("<b>🎯 TOP 5 SCORES PROBABLES:</b>")
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for i, (score_tuple, prob_pct) in enumerate(prediction.get("top_scores", [])[:5]):
        lines.append(f"  {medals[i]} {score_tuple[0]}-{score_tuple[1]} ({prob_pct}%)")

    # Conseil
    lines.append("")
    lines.append("<b>💡 CONSEIL:</b>")
    if prob["home_win"] > 55:
        lines.append(
            f"  ✅ Victoire probable de {prediction['home_team']} ({prob['home_win']}%)"
        )
    elif prob["away_win"] > 55:
        lines.append(
            f"  ✅ Victoire probable de {prediction['away_team']} ({prob['away_win']}%)"
        )
    else:
        lines.append(f"  ⚠️ Match équilibré - Nul possible ({prob['draw']}%)")

    if btts > 55:
        lines.append(f"  ✅ BTTS recommandé ({btts}%)")
    if over25 > 55:
        lines.append(f"  ✅ Over 2.5 recommandé ({over25}%)")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────
# COMMANDES TELEGRAM
# ─────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /start - Message de bienvenue."""
    welcome = (
        "⚽ <b>LIGUE 1 PREDICTOR BOT 2025-2026</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Bienvenue ! Je prédis les <b>titularisations</b>, "
        "<b>résultats</b> et <b>meilleures cotes</b> des matchs de Ligue 1.\n\n"
        "⭐⭐⭐ <b>NOS PARTENAIRES</b> ⭐⭐⭐\n\n"
        "🎰 <a href=\"https://shuffle.com?r=53pvu4tm6c\"><b>SHUFFLE</b></a>"
        " - Plateforme crypto #1\n"
        "   🎁 Bonus crypto exclusif\n\n"
        "🔥 <a href=\"https://betfury.com/?r=User7584362\"><b>BETFURY</b></a>"
        " - Paris sportifs & Casino crypto\n"
        "   🎁 Bonus inscription\n"
        "   📋 Code parrainage: <code>User7584362</code>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>📋 COMMANDES:</b>\n\n"
        "🏟 <b>/equipe</b> <i>nom</i>\n"
        "   → Analyse complète d'une équipe\n"
        "   Ex: <code>/equipe Lyon</code>\n\n"
        "⚔️ <b>/match</b> <i>domicile exterieur</i>\n"
        "   → Prédiction de match complète\n"
        "   Ex: <code>/match PSG OM</code>\n\n"
        "💰 <b>/cotes</b> <i>domicile exterieur</i>\n"
        "   → Meilleures cotes bookmakers\n"
        "   Ex: <code>/cotes PSG Lyon</code>\n\n"
        "📋 <b>/liste</b>\n"
        "   → Liste des 18 équipes\n\n"
        "ℹ️ <b>/aide</b>\n"
        "   → Aide détaillée\n\n"
        "💡 <i>Ou tapez simplement le nom d'une équipe !</i>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>⚠️ Jeu responsable. 18+ uniquement.</i>"
    )

    # Boutons d'action rapide - Partenaires en premier
    keyboard = [
        [
            InlineKeyboardButton(
                "⭐🎰 SHUFFLE - Bonus Crypto",
                url="https://shuffle.com?r=53pvu4tm6c",
            ),
        ],
        [
            InlineKeyboardButton(
                "⭐🔥 BETFURY - Code: User7584362",
                url="https://betfury.com/?r=User7584362",
            ),
        ],
        [
            InlineKeyboardButton("⚽ PSG", callback_data="team_psg"),
            InlineKeyboardButton("⚽ OM", callback_data="team_om"),
            InlineKeyboardButton("⚽ OL", callback_data="team_ol"),
        ],
        [
            InlineKeyboardButton("⚔️ PSG vs OM", callback_data="match_psg_om"),
            InlineKeyboardButton("⚔️ OL vs PSG", callback_data="match_ol_psg"),
        ],
        [
            InlineKeyboardButton("📋 Toutes les équipes", callback_data="list_teams"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome, parse_mode=ParseMode.HTML, reply_markup=reply_markup
    )


async def cmd_aide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /aide - Aide détaillée."""
    help_text = (
        "ℹ️ <b>AIDE - LIGUE 1 PREDICTOR</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>🏟 /equipe &lt;nom&gt;</b>\n"
        "Analyse complète d'une équipe:\n"
        "• XI de départ prédit\n"
        "• Joueurs blessés/suspendus\n"
        "• Forme récente et prochains matchs\n"
        "• Effectif complet avec ratings\n\n"
        "<b>⚔️ /match &lt;dom&gt; &lt;ext&gt;</b>\n"
        "Prédiction de match complète:\n"
        "• XI de départ des 2 équipes\n"
        "• Probabilités 1X2\n"
        "• Score prédit + top 5 scores\n"
        "• BTTS, Over/Under\n"
        "• Meilleures cotes avec liens\n\n"
        "<b>💰 /cotes &lt;dom&gt; &lt;ext&gt;</b>\n"
        "Meilleures cotes uniquement:\n"
        "• Top 4 bookmakers par marché\n"
        "• Liens directs pour parier\n"
        "• Bonus d'inscription\n\n"
        "<b>📋 /liste</b>\n"
        "Liste des 18 clubs de Ligue 1\n\n"
        "<b>💡 Noms acceptés:</b>\n"
        "PSG, Paris, OM, Marseille, OL, Lyon,\n"
        "Monaco, Lille, LOSC, Lens, Nice, Rennes,\n"
        "Toulouse, Brest, Strasbourg, Nantes,\n"
        "Angers, Auxerre, Le Havre, Lorient,\n"
        "Paris FC, Metz\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>⚠️ Prédictions à titre indicatif.\n"
        "Pariez de manière responsable. 18+</i>"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)


async def cmd_liste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /liste - Liste des équipes."""
    lines = ["📋 <b>EQUIPES LIGUE 1 2025-2026</b>", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", ""]

    for i, (key, team) in enumerate(LIGUE1_TEAMS.items(), 1):
        lines.append(
            f"{i:2d}. <b>{team['full_name']}</b>\n"
            f"     👔 {team['coach']} | 📐 {'/'.join(team['preferred_formations'])}"
        )

    lines.append("")
    lines.append("<i>Tapez /equipe suivi du nom pour analyser une équipe</i>")
    lines.append("<i>Ex: /equipe Lyon</i>")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def cmd_equipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /equipe <nom> - Analyse d'une équipe."""
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: <code>/equipe nom_equipe</code>\n"
            "Ex: <code>/equipe Lyon</code> ou <code>/equipe PSG</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    team_query = " ".join(context.args)
    await _analyze_team(update, team_query)


async def _analyze_team(update: Update, team_query: str, message=None):
    """Logique d'analyse d'équipe (réutilisable)."""
    team = find_team(team_query)
    team_key = find_team_key(team_query)

    if not team:
        await (message or update.message).reply_text(
            f"❌ Équipe '<b>{team_query}</b>' non trouvée.\n"
            f"Tapez /liste pour voir les équipes disponibles.",
            parse_mode=ParseMode.HTML,
        )
        return

    target = message or update.message
    await target.reply_text("⏳ Analyse en cours...", parse_mode=ParseMode.HTML)

    # Récupérer données live (v2 avec compositions réelles)
    team_id = team.get("api_football_id", 0)
    live_data = await fetcher.get_all_team_data_v2(team_id, team["full_name"])

    injuries = []
    suspensions = []
    for inj in live_data.get("injuries", []):
        reason = inj.get("reason", "").lower()
        if "suspended" in reason or "card" in reason:
            suspensions.append(inj["player_name"])
        else:
            injuries.append(inj["player_name"])

    # Prédire la composition (avec données live si disponibles)
    lineup = predictor.predict_lineup(team_key, injuries, suspensions, live_data=live_data)

    # Coach en temps réel si disponible
    coach_name = live_data.get("coach", {}).get("name") or team["coach"]
    data_source = lineup.get("data_source", "static")
    if data_source == "live":
        source_label = "📡 Données temps réel"
    else:
        source_label = "⚠️ Données de base (effectifs possiblement obsolètes)"

    # Info équipe
    info_text = (
        f"🏟 <b>{team['full_name']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👔 Coach: <b>{coach_name}</b>\n"
        f"🏟 Stade: {team['stadium']}, {team['city']}\n"
        f"📐 Formations: {' / '.join(team['preferred_formations'])}\n"
        f"🎯 Style: <i>{team['style']}</i>\n"
        f"{source_label}\n"
    )
    await target.reply_text(info_text, parse_mode=ParseMode.HTML)

    # XI de départ
    lineup_text = format_lineup_telegram(lineup)
    await target.reply_text(lineup_text, parse_mode=ParseMode.HTML)

    # Boutons vers bookmakers - Partenaires en premier
    keyboard = [
        [
            InlineKeyboardButton(
                "⭐🎰 SHUFFLE - Bonus Crypto",
                url="https://shuffle.com?r=53pvu4tm6c",
            ),
        ],
        [
            InlineKeyboardButton(
                "⭐🔥 BETFURY - Code: User7584362",
                url="https://betfury.com/?r=User7584362",
            ),
        ],
    ]
    row = []
    for bm_name in ["Betclic", "Winamax", "Unibet", "1xBet"]:
        bm_info = get_bookmaker_info(bm_name)
        row.append(
            InlineKeyboardButton(
                f"{bm_info['logo']} {bm_name}",
                url=bm_info["link"],
            )
        )
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    await target.reply_text(
        f"💰 <b>Parier sur {team['short_name']}:</b>\n\n"
        f"⭐ <b>Recommandés:</b>\n"
        f"🎰 <a href=\"https://shuffle.com?r=53pvu4tm6c\">Shuffle</a> - Bonus crypto exclusif\n"
        f"🔥 <a href=\"https://betfury.com/?r=User7584362\">BetFury</a> - Code: <code>User7584362</code>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True,
    )


async def cmd_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /match <dom> <ext> - Prédiction de match."""
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Usage: <code>/match equipe_dom equipe_ext</code>\n"
            "Ex: <code>/match PSG OM</code> ou <code>/match Lyon Marseille</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    home_query = context.args[0]
    away_query = " ".join(context.args[1:])
    await _analyze_match(update, home_query, away_query)


async def _analyze_match(update: Update, home_query: str, away_query: str, message=None):
    """Logique d'analyse de match (réutilisable)."""
    home_key = find_team_key(home_query)
    away_key = find_team_key(away_query)

    target = message or update.message

    if not home_key or home_key not in LIGUE1_TEAMS:
        await target.reply_text(
            f"❌ Équipe domicile '<b>{home_query}</b>' non trouvée.\nTapez /liste",
            parse_mode=ParseMode.HTML,
        )
        return

    if not away_key or away_key not in LIGUE1_TEAMS:
        await target.reply_text(
            f"❌ Équipe extérieur '<b>{away_query}</b>' non trouvée.\nTapez /liste",
            parse_mode=ParseMode.HTML,
        )
        return

    home_team = LIGUE1_TEAMS[home_key]
    away_team = LIGUE1_TEAMS[away_key]

    await target.reply_text(
        f"⏳ Analyse du match <b>{home_team['full_name']} vs {away_team['full_name']}</b>...",
        parse_mode=ParseMode.HTML,
    )

    # Récupérer données live (v2 avec compositions réelles)
    home_data, away_data = await asyncio.gather(
        fetcher.get_all_team_data_v2(home_team["api_football_id"], home_team["full_name"]),
        fetcher.get_all_team_data_v2(away_team["api_football_id"], away_team["full_name"]),
    )

    home_injuries, home_suspensions = _extract_unavailable(home_data)
    away_injuries, away_suspensions = _extract_unavailable(away_data)

    home_form = home_data.get("stats", {}).get("form", "")
    away_form = away_data.get("stats", {}).get("form", "")

    # Analyse avec données live
    analysis = predictor.generate_match_analysis(
        home_key, away_key,
        home_injuries, away_injuries,
        home_suspensions, away_suspensions,
        home_form, away_form,
        home_live_data=home_data,
        away_live_data=away_data,
    )

    # 1. En-tête match
    header = (
        f"⚽ <b>ANALYSE DU MATCH</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏠 <b>{home_team['full_name']}</b>\n"
        f"        ⚔️ vs\n"
        f"✈️ <b>{away_team['full_name']}</b>\n"
        f"🏟 {home_team['stadium']}, {home_team['city']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    await target.reply_text(header, parse_mode=ParseMode.HTML)

    # 2. Compo domicile
    home_lineup_text = format_lineup_telegram(analysis["home_lineup"], side="home")
    await target.reply_text(home_lineup_text, parse_mode=ParseMode.HTML)

    # 3. Compo extérieur
    away_lineup_text = format_lineup_telegram(analysis["away_lineup"], side="away")
    await target.reply_text(away_lineup_text, parse_mode=ParseMode.HTML)

    # 4. Prédictions
    pred_text = format_prediction_telegram(analysis["prediction"])
    await target.reply_text(pred_text, parse_mode=ParseMode.HTML)

    # 5. Cotes avec liens d'affiliation
    odds = await fetcher.get_best_odds(home_team["full_name"], away_team["full_name"])
    odds_text = format_odds_message_telegram(odds, home_team["short_name"], away_team["short_name"])

    # Boutons bookmakers
    button_rows = format_quick_odds_buttons(odds, home_team["short_name"], away_team["short_name"])
    keyboard = [
        [InlineKeyboardButton(btn["text"], url=btn["url"]) for btn in row]
        for row in button_rows
    ]

    await target.reply_text(
        odds_text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
        disable_web_page_preview=True,
    )


async def cmd_cotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /cotes <dom> <ext> - Meilleures cotes uniquement."""
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Usage: <code>/cotes equipe_dom equipe_ext</code>\n"
            "Ex: <code>/cotes PSG OM</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    home_query = context.args[0]
    away_query = " ".join(context.args[1:])

    home_key = find_team_key(home_query)
    away_key = find_team_key(away_query)

    if not home_key or not away_key:
        await update.message.reply_text("❌ Équipe(s) non trouvée(s). Tapez /liste")
        return

    home_team = LIGUE1_TEAMS[home_key]
    away_team = LIGUE1_TEAMS[away_key]

    await update.message.reply_text("⏳ Récupération des cotes...")

    odds = await fetcher.get_best_odds(home_team["full_name"], away_team["full_name"])
    odds_text = format_odds_message_telegram(odds, home_team["short_name"], away_team["short_name"])

    button_rows = format_quick_odds_buttons(odds, home_team["short_name"], away_team["short_name"])
    keyboard = [
        [InlineKeyboardButton(btn["text"], url=btn["url"]) for btn in row]
        for row in button_rows
    ]

    await update.message.reply_text(
        odds_text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
        disable_web_page_preview=True,
    )


# ─────────────────────────────────────────────────────────
# CALLBACK QUERIES (boutons inline)
# ─────────────────────────────────────────────────────────

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère les clics sur les boutons inline."""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "list_teams":
        lines = ["📋 <b>EQUIPES LIGUE 1 2025-2026</b>", ""]
        for i, (key, team) in enumerate(LIGUE1_TEAMS.items(), 1):
            lines.append(f"{i}. <b>{team['full_name']}</b> ({key.upper()})")
        lines.append("\nTapez /equipe suivi du nom pour analyser")
        await query.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

    elif data.startswith("team_"):
        team_key = data.replace("team_", "")
        await _analyze_team(update, team_key, message=query.message)

    elif data.startswith("match_"):
        parts = data.replace("match_", "").split("_")
        if len(parts) >= 2:
            await _analyze_match(update, parts[0], parts[1], message=query.message)


# ─────────────────────────────────────────────────────────
# MESSAGE HANDLER (texte libre)
# ─────────────────────────────────────────────────────────

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère les messages texte libres - détecte les noms d'équipes."""
    text = update.message.text.strip()

    # Détecter "X vs Y" ou "X - Y"
    for sep in [" vs ", " - ", " contre "]:
        if sep in text.lower():
            parts = text.lower().split(sep)
            if len(parts) == 2:
                home = parts[0].strip()
                away = parts[1].strip()
                if find_team_key(home) and find_team_key(away):
                    await _analyze_match(update, home, away)
                    return

    # Détecter un nom d'équipe seul
    team = find_team(text)
    if team:
        await _analyze_team(update, text)
        return

    # Message non reconnu
    await update.message.reply_text(
        "🤔 Je n'ai pas compris. Essayez:\n\n"
        "• Le nom d'une équipe: <code>Lyon</code>\n"
        "• Un match: <code>PSG vs OM</code>\n"
        "• /aide pour l'aide complète",
        parse_mode=ParseMode.HTML,
    )


# ─────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────

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
# MAIN
# ─────────────────────────────────────────────────────────

def main():
    """Lance le bot Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        print("=" * 50)
        print("ERREUR: TELEGRAM_BOT_TOKEN non défini!")
        print("=" * 50)
        print()
        print("Pour configurer le bot:")
        print("1. Parlez à @BotFather sur Telegram")
        print("2. Créez un bot avec /newbot")
        print("3. Copiez le token")
        print("4. Lancez avec:")
        print()
        print("   TELEGRAM_BOT_TOKEN='votre_token' python ligue1_telegram_bot.py")
        print()
        print("Variables optionnelles:")
        print("   API_FOOTBALL_KEY    - Données live (api-football.com)")
        print("   ODDS_API_KEY        - Cotes live (the-odds-api.com)")
        print()
        print("Variables d'affiliation (optionnelles):")
        for bm_name, config in BOOKMAKER_CONFIG.items():
            print(f"   {config['env_var']:30s} - {bm_name}")
        print()
        return

    print("⚽ Ligue 1 Predictor Bot - Démarrage...")
    print(f"   API Football: {'✅ Configurée' if os.getenv('API_FOOTBALL_KEY') else '❌ Non configurée (données simulées)'}")
    print(f"   Odds API:     {'✅ Configurée' if os.getenv('ODDS_API_KEY') else '❌ Non configurée (cotes simulées)'}")

    # Compter les affiliations configurées
    affil_count = sum(1 for cfg in BOOKMAKER_CONFIG.values() if os.getenv(cfg["env_var"]))
    print(f"   Affiliations: {affil_count}/{len(BOOKMAKER_CONFIG)} configurées")
    print()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Commandes
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("aide", cmd_aide))
    app.add_handler(CommandHandler("help", cmd_aide))
    app.add_handler(CommandHandler("liste", cmd_liste))
    app.add_handler(CommandHandler("list", cmd_liste))
    app.add_handler(CommandHandler("equipe", cmd_equipe))
    app.add_handler(CommandHandler("team", cmd_equipe))
    app.add_handler(CommandHandler("match", cmd_match))
    app.add_handler(CommandHandler("cotes", cmd_cotes))
    app.add_handler(CommandHandler("odds", cmd_cotes))

    # Callbacks (boutons inline)
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Messages texte libres
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("✅ Bot démarré! En attente de messages...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
