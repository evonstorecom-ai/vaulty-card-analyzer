"""
Configuration des liens d'affiliation pour les bookmakers.
Chaque bookmaker a un lien de base avec un paramètre de tracking.

Pour configurer vos liens d'affiliation:
1. Inscrivez-vous sur les plateformes d'affiliation de chaque bookmaker
2. Récupérez votre identifiant affilié (btag, affid, etc.)
3. Configurez les variables d'environnement correspondantes

Plateformes d'affiliation recommandées:
- Betclic Partners    -> https://partners.betclic.com
- Winamax Affiliés    -> https://affiliates.winamax.fr
- Unibet Affiliates   -> https://www.unibetaffiliates.com
- 1xBet Partners      -> https://partners.1xbet.com
- Bwin Partners       -> https://partners.bwin.com
- PMU Partenaires     -> https://www.pmu.fr/partenaires
- ParionsSport (FDJ)  -> Contact direct FDJ
- Betway Partners     -> https://www.betwaypartners.com
- Zebet Affiliés      -> https://www.zebet.fr/affiliation
- Vbet Affiliates     -> https://affiliates.vbet.com
"""

import os


# ─────────────────────────────────────────────────────────
# CONFIGURATION DES LIENS D'AFFILIATION
# ─────────────────────────────────────────────────────────

# Format: chaque bookmaker a un lien de base et un paramètre de tracking
# Le système remplace {AFFILIATE_ID} par votre ID et {EVENT} par le match

# ─── PLATEFORMES PARTENAIRES (affichées en priorité) ───

FEATURED_PLATFORMS = {
    "Shuffle": {
        "affiliate_url": "https://shuffle.com?r=53pvu4tm6c",
        "logo": "🎰",
        "bonus": "Bonus crypto exclusif",
        "description": "Plateforme crypto #1 - Paris sportifs & Casino",
        "featured": True,
    },
    "BetFury": {
        "affiliate_url": "https://betfury.com/?r=User7584362",
        "referral_code": "User7584362",
        "logo": "🔥",
        "bonus": "Bonus inscription + crypto",
        "description": "Paris sportifs & Casino crypto - Code: User7584362",
        "featured": True,
    },
}

# ─── BOOKMAKERS CLASSIQUES ───

BOOKMAKER_CONFIG = {
    "Shuffle": {
        "base_url": "https://shuffle.com",
        "affiliate_url": "https://shuffle.com?r=53pvu4tm6c",
        "env_var": "SHUFFLE_AFFILIATE_ID",
        "default_link": "https://shuffle.com?r=53pvu4tm6c",
        "logo": "🎰",
        "bonus": "Bonus crypto exclusif",
        "featured": True,
    },
    "BetFury": {
        "base_url": "https://betfury.com",
        "affiliate_url": "https://betfury.com/?r=User7584362",
        "env_var": "BETFURY_AFFILIATE_ID",
        "default_link": "https://betfury.com/?r=User7584362",
        "logo": "🔥",
        "bonus": "Bonus + Code: User7584362",
        "referral_code": "User7584362",
        "featured": True,
    },
    "Betclic": {
        "base_url": "https://www.betclic.fr/football-s1/ligue-1-c4",
        "affiliate_url": "https://www.betclic.fr/?btag={AFFILIATE_ID}",
        "env_var": "BETCLIC_AFFILIATE_ID",
        "default_link": "https://www.betclic.fr/football-s1/ligue-1-c4",
        "logo": "🟡",
        "bonus": "Jusqu'à 100€ offerts",
        "featured": False,
    },
    "Winamax": {
        "base_url": "https://www.winamax.fr/paris-sportifs/sports/1/7/4",
        "affiliate_url": "https://www.winamax.fr/?wm={AFFILIATE_ID}",
        "env_var": "WINAMAX_AFFILIATE_ID",
        "default_link": "https://www.winamax.fr/paris-sportifs/sports/1/7/4",
        "logo": "🔴",
        "bonus": "Jusqu'à 100€ de freebets",
        "featured": False,
    },
    "Unibet": {
        "base_url": "https://www.unibet.fr/sport/football/france/ligue-1",
        "affiliate_url": "https://www.unibet.fr/?utm_source=affiliate&utm_medium={AFFILIATE_ID}",
        "env_var": "UNIBET_AFFILIATE_ID",
        "default_link": "https://www.unibet.fr/sport/football/france/ligue-1",
        "logo": "🟢",
        "bonus": "Jusqu'à 100€ offerts",
        "featured": False,
    },
    "1xBet": {
        "base_url": "https://1xbet.com/fr/line/football/12821-france-ligue-1",
        "affiliate_url": "https://refpa7921972.top/L?tag={AFFILIATE_ID}",
        "env_var": "ONEXBET_AFFILIATE_ID",
        "default_link": "https://1xbet.com/fr/line/football/12821-france-ligue-1",
        "logo": "🔵",
        "bonus": "Bonus 100% jusqu'à 130€",
        "featured": False,
    },
    "PMU": {
        "base_url": "https://paris-sportifs.pmu.fr/football/ligue-1",
        "affiliate_url": "https://paris-sportifs.pmu.fr/?affilid={AFFILIATE_ID}",
        "env_var": "PMU_AFFILIATE_ID",
        "default_link": "https://paris-sportifs.pmu.fr/football/ligue-1",
        "logo": "🟤",
        "bonus": "Jusqu'à 100€ offerts",
        "featured": False,
    },
    "ParionsSport": {
        "base_url": "https://www.enligne.parionssport.fdj.fr/football/france/ligue-1",
        "affiliate_url": "https://www.enligne.parionssport.fdj.fr/?affid={AFFILIATE_ID}",
        "env_var": "PARIONSSPORT_AFFILIATE_ID",
        "default_link": "https://www.enligne.parionssport.fdj.fr/football/france/ligue-1",
        "logo": "🔷",
        "bonus": "Jusqu'à 85€ de freebets",
        "featured": False,
    },
    "Bwin": {
        "base_url": "https://www.bwin.fr/sports/football/france/ligue-1",
        "affiliate_url": "https://www.bwin.fr/?wm={AFFILIATE_ID}",
        "env_var": "BWIN_AFFILIATE_ID",
        "default_link": "https://www.bwin.fr/sports/football/france/ligue-1",
        "logo": "⚫",
        "bonus": "Jusqu'à 120€ offerts",
        "featured": False,
    },
    "Zebet": {
        "base_url": "https://www.zebet.fr/fr/competition/96-ligue_1_uber_eats",
        "affiliate_url": "https://www.zebet.fr/?affid={AFFILIATE_ID}",
        "env_var": "ZEBET_AFFILIATE_ID",
        "default_link": "https://www.zebet.fr/fr/competition/96-ligue_1_uber_eats",
        "logo": "🟣",
        "bonus": "Jusqu'à 150€ offerts",
        "featured": False,
    },
}


def get_affiliate_link(bookmaker: str) -> str:
    """
    Retourne le lien d'affiliation pour un bookmaker.
    Les plateformes partenaires (Shuffle, BetFury) ont des liens fixes.
    Pour les autres, utilise la variable d'environnement si configurée.
    """
    config = BOOKMAKER_CONFIG.get(bookmaker)
    if not config:
        return f"https://www.google.com/search?q={bookmaker}+paris+sportifs+ligue+1"

    # Plateformes partenaires: lien fixe direct
    if config.get("featured"):
        return config["affiliate_url"]

    # Autres: vérifier la variable d'environnement
    affiliate_id = os.getenv(config["env_var"], "")
    if affiliate_id:
        return config["affiliate_url"].replace("{AFFILIATE_ID}", affiliate_id)
    else:
        return config["default_link"]


def get_bookmaker_info(bookmaker: str) -> dict:
    """Retourne les infos complètes d'un bookmaker."""
    config = BOOKMAKER_CONFIG.get(bookmaker, {})
    return {
        "name": bookmaker,
        "link": get_affiliate_link(bookmaker),
        "logo": config.get("logo", "📌"),
        "bonus": config.get("bonus", ""),
        "featured": config.get("featured", False),
        "referral_code": config.get("referral_code", ""),
    }


def get_featured_platforms() -> list[dict]:
    """Retourne les plateformes partenaires mises en avant."""
    return [get_bookmaker_info(name) for name, cfg in BOOKMAKER_CONFIG.items() if cfg.get("featured")]


def get_all_bookmakers_with_links() -> list[dict]:
    """Retourne tous les bookmakers avec leurs liens d'affiliation."""
    return [get_bookmaker_info(name) for name in BOOKMAKER_CONFIG]


def format_featured_banner() -> str:
    """Génère la bannière des plateformes partenaires pour Telegram (HTML)."""
    lines = []
    lines.append("⭐⭐⭐ <b>NOS PARTENAIRES RECOMMANDÉS</b> ⭐⭐⭐")
    lines.append("")

    for name, platform in FEATURED_PLATFORMS.items():
        lines.append(
            f"{platform['logo']} <b><a href=\"{platform['affiliate_url']}\">"
            f"{name}</a></b> - {platform['description']}"
        )
        if platform.get("referral_code"):
            lines.append(
                f"   📋 Code parrainage: <code>{platform['referral_code']}</code>"
            )
        lines.append(f"   🎁 {platform['bonus']}")
        lines.append("")

    return "\n".join(lines)


def format_odds_message_telegram(
    odds_data: dict,
    home_team: str,
    away_team: str,
) -> str:
    """
    Formate les cotes avec liens d'affiliation pour Telegram.
    Met en avant Shuffle et BetFury en priorité.
    """
    if not odds_data:
        return "⚠️ Aucune cote disponible pour le moment."

    lines = []

    # Bannière partenaires en haut
    lines.append(format_featured_banner())
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")

    lines.append(f"💰 <b>MEILLEURES COTES</b>")
    lines.append(f"📊 <b>{home_team} vs {away_team}</b>")
    lines.append("")

    markets = [
        ("home_win", f"🏠 Victoire {home_team}"),
        ("draw", "🤝 Match Nul"),
        ("away_win", f"✈️ Victoire {away_team}"),
        ("over_2_5", "⬆️ Plus de 2.5 buts"),
        ("under_2_5", "⬇️ Moins de 2.5 buts"),
    ]

    for market_key, market_label in markets:
        if market_key not in odds_data or not odds_data[market_key]:
            continue

        lines.append(f"<b>{market_label}:</b>")

        for i, odd in enumerate(odds_data[market_key][:4], 1):
            bm_name = odd["bookmaker"]
            bm_info = get_bookmaker_info(bm_name)
            link = bm_info["link"]
            logo = bm_info["logo"]

            medal = ["🥇", "🥈", "🥉", "4️⃣"][i - 1]
            lines.append(
                f"  {medal} {logo} <a href=\"{link}\">{bm_name}</a> "
                f"→ <b>{odd['odds']:.2f}</b>"
            )

        lines.append("")

    # Section bonus avec partenaires en premier
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("🎁 <b>BONUS & INSCRIPTIONS:</b>")
    lines.append("")

    # Partenaires mis en avant en premier
    for name, platform in FEATURED_PLATFORMS.items():
        lines.append(
            f"  ⭐ {platform['logo']} <a href=\"{platform['affiliate_url']}\">"
            f"<b>{name}</b></a> - {platform['bonus']}"
        )
        if platform.get("referral_code"):
            lines.append(
                f"     📋 Code: <code>{platform['referral_code']}</code>"
            )

    lines.append("")

    # Puis les autres bookmakers
    seen = set(FEATURED_PLATFORMS.keys())
    for market_key in ["home_win", "draw", "away_win"]:
        for odd in odds_data.get(market_key, [])[:4]:
            bm_name = odd["bookmaker"]
            if bm_name in seen:
                continue
            seen.add(bm_name)
            bm_info = get_bookmaker_info(bm_name)
            if bm_info["bonus"]:
                lines.append(
                    f"  {bm_info['logo']} <a href=\"{bm_info['link']}\">{bm_name}</a>"
                    f" - {bm_info['bonus']}"
                )

    lines.append("")
    lines.append("<i>⚠️ Jeu responsable. 18+ | Les cotes peuvent varier.</i>")

    return "\n".join(lines)


def format_quick_odds_buttons(odds_data: dict, home_team: str, away_team: str) -> list[list[dict]]:
    """
    Génère les boutons inline Telegram avec les bookmakers.
    Shuffle et BetFury toujours en première ligne.
    """
    buttons = []

    # TOUJOURS mettre les partenaires en premier
    for name, platform in FEATURED_PLATFORMS.items():
        label = f"⭐ {platform['logo']} {name}"
        if platform.get("referral_code"):
            label += f" (Code: {platform['referral_code']})"
        else:
            label += f" - {platform['bonus'][:18]}"
        buttons.append({
            "text": label,
            "url": platform["affiliate_url"],
        })

    # Puis les autres bookmakers des cotes
    seen = set(FEATURED_PLATFORMS.keys())
    for market_key in ["home_win", "draw", "away_win"]:
        for odd in odds_data.get(market_key, [])[:4]:
            bm_name = odd["bookmaker"]
            if bm_name not in seen:
                seen.add(bm_name)
                bm_info = get_bookmaker_info(bm_name)
                buttons.append({
                    "text": f"{bm_info['logo']} {bm_name} - {bm_info['bonus'][:20]}",
                    "url": bm_info["link"],
                })

    # Organiser en lignes de 2 boutons
    rows = []
    for i in range(0, min(len(buttons), 10), 2):
        row = buttons[i:i + 2]
        rows.append(row)

    return rows
