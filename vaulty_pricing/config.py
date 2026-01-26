"""
Vaulty Pricing Configuration
Price factors and multipliers for card valuation
"""

# Grade multipliers (PSA 8 = base reference at 1.0)
GRADE_MULTIPLIERS = {
    # PSA Grades
    "PSA 10": 8.0,
    "PSA 9": 2.5,
    "PSA 8": 1.0,
    "PSA 7": 0.6,
    "PSA 6": 0.4,
    "PSA 5": 0.25,
    "PSA 4": 0.15,
    "PSA 3": 0.10,
    "PSA 2": 0.08,
    "PSA 1": 0.05,
    # BGS Grades
    "BGS 10": 12.0,  # Black Label
    "BGS 9.5": 3.5,
    "BGS 9": 2.0,
    "BGS 8.5": 1.3,
    "BGS 8": 1.0,
    # SGC Grades
    "SGC 10": 4.0,
    "SGC 9.5": 2.8,
    "SGC 9": 2.0,
    "SGC 8": 0.9,
    # CGC Grades
    "CGC 10": 3.0,
    "CGC 9.5": 2.2,
    "CGC 9": 1.8,
    # RAW (ungraded)
    "RAW": 0.3,
    "RAW_MINT": 0.5,
    "RAW_NM": 0.35,
    "RAW_EX": 0.2,
    "RAW_VG": 0.1,
}

# Player tier multipliers
PLAYER_TIERS = {
    "GOAT": 10.0,       # Michael Jordan, LeBron James, Messi, Ronaldo, Brady
    "legend": 6.0,      # Kobe, Magic, Bird, Maradona, Pelé
    "superstar": 4.0,   # Curry, Durant, Giannis, Neymar, Mbappé
    "star": 2.0,        # Current All-Stars, good players
    "starter": 1.2,     # Solid starters
    "role_player": 1.0, # Standard players (base)
    "bench": 0.7,       # Bench players
    "bust": 0.3,        # Draft busts (Darko, Kwame, etc.)
    "unknown": 0.5,     # Unknown players
}

# Card type/rarity multipliers
RARITY_MULTIPLIERS = {
    # Base types
    "base": 1.0,
    "common": 0.8,

    # Parallels
    "parallel": 2.0,
    "silver": 1.5,
    "gold": 3.0,
    "platinum": 5.0,

    # Refractors & special finishes
    "refractor": 3.0,
    "prizm": 2.5,
    "holo": 2.0,
    "chrome": 2.0,
    "atomic": 4.0,
    "xfractor": 3.5,
    "superfractor": 25.0,

    # Numbered cards
    "numbered_999": 1.3,
    "numbered_499": 1.5,
    "numbered_299": 2.0,
    "numbered_199": 2.5,
    "numbered_99": 3.5,
    "numbered_50": 5.0,
    "numbered_25": 8.0,
    "numbered_10": 12.0,
    "numbered_5": 20.0,
    "1/1": 50.0,

    # Special cards
    "rookie": 2.0,
    "auto": 5.0,
    "auto_rookie": 8.0,
    "patch": 4.0,
    "jersey": 2.5,
    "auto_patch": 10.0,
    "auto_patch_rookie": 15.0,
    "logoman": 30.0,

    # Insert sets
    "insert": 1.5,
    "ssp": 4.0,  # Short print
    "ssp": 8.0,  # Super short print
}

# Set prestige multipliers (how desirable is the set)
SET_MULTIPLIERS = {
    # Basketball - Premium
    "Panini National Treasures": 5.0,
    "Panini Flawless": 6.0,
    "Panini Immaculate": 4.0,
    "Topps Chrome": 2.5,
    "Panini Prizm": 2.0,
    "Panini Select": 1.8,
    "Panini Mosaic": 1.5,
    "Upper Deck Exquisite": 5.0,

    # Basketball - Standard
    "Panini Donruss": 1.2,
    "Panini Hoops": 1.0,
    "Topps": 1.3,
    "Fleer": 1.5,
    "Upper Deck": 1.4,

    # Basketball - Vintage
    "1986 Fleer": 8.0,
    "1996 Topps Chrome": 4.0,
    "2003 Topps Chrome": 3.5,

    # Football - Premium
    "Panini National Treasures Football": 5.0,
    "Panini Prizm Football": 2.0,

    # Pokemon
    "Base Set": 3.0,
    "Base Set 1st Edition": 10.0,
    "Shadowless": 5.0,
    "Japanese": 0.7,

    # Default
    "default": 1.0,
}

# Year/rookie adjustments
YEAR_ADJUSTMENTS = {
    "rookie_year": 2.0,
    "2nd_year": 1.3,
    "3rd_year": 1.1,
    "veteran": 1.0,
    "retired_recent": 0.9,
    "retired_long": 0.7,
}

# Population adjustments (PSA pop report)
POPULATION_MULTIPLIERS = {
    "pop_1": 5.0,
    "pop_2_5": 3.5,
    "pop_6_10": 2.5,
    "pop_11_25": 2.0,
    "pop_26_50": 1.5,
    "pop_51_100": 1.2,
    "pop_101_250": 1.0,
    "pop_251_500": 0.9,
    "pop_501_1000": 0.8,
    "pop_1001_plus": 0.6,
}

# Sport/Category base prices (average card PSA 8 value)
CATEGORY_BASE_PRICES = {
    "Basketball": 15.0,
    "Football": 12.0,
    "Baseball": 10.0,
    "Hockey": 8.0,
    "Soccer": 12.0,
    "Pokemon": 20.0,
    "Magic: The Gathering": 15.0,
    "Yu-Gi-Oh!": 10.0,
    "Other TCG": 8.0,
    "default": 10.0,
}

# Confidence thresholds
CONFIDENCE_THRESHOLDS = {
    "verified": 0.90,      # Verified in database
    "high": 0.75,          # Strong algorithm match
    "medium": 0.60,        # Calculated estimate
    "low": 0.40,           # Rough estimate
    "none": 0.0,           # Cannot estimate
}

# Minimum confidence to show price
MIN_CONFIDENCE_TO_DISPLAY = 0.50

# Price staleness (days before price needs re-verification)
PRICE_STALENESS_DAYS = 90

# Currency settings
DEFAULT_CURRENCY = "USD"
CURRENCY_SYMBOLS = {
    "USD": "$",
    "EUR": "€",
    "CHF": "CHF",
    "GBP": "£",
}

# Admin user IDs (Telegram) - add your user ID here
ADMIN_USER_IDS = []
