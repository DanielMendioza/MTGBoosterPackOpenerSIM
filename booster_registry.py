from typing import Dict, Any

MYTHIC_CHANCE = 0.125

# Five allied fetches (left here if you enable an MH3 foil-fetch lottery)
FETCHLAND_NAMES = {
    "Arid Mesa", "Marsh Flats", "Misty Rainforest", "Scalding Tarn", "Verdant Catacombs"
}

# DSK collector numbers for Lurking Evil (from your file)
LURKING_EVIL_COLLECTOR_NUMBERS = {
    "common":   ["287","295"],
    "uncommon": ["288","291","297","300"],
    "rare":     ["289","290","292","294","296","299","301"],
    "mythic":   ["293","298"],
}

# -----------------------------
# DEFAULT (fallback template)
# -----------------------------
REGISTRY: Dict[str, Dict[str, Any]] = {
    "_default": dict(
        set_code="",
        common_slots=6,
        uncommon_slots=3,

        # If you use simple rarity splits instead of a table:
        rare_weights={"rare": 1 - MYTHIC_CHANCE, "mythic": MYTHIC_CHANCE},
        wildcard_weights={"common": 0.50, "uncommon": 0.30, "rare": 0.15, "mythic": 0.05},
        foil_weights={"common": 0.65, "uncommon": 0.25, "rare": 0.08, "mythic": 0.02},

        # Tables (optional): arrays of weighted entries with exact queries
        #  - Each entry: {"weight": float, "treatment": "label", "query": "...", "foil": bool?}
        #  - If table provided, it overrides the simple weights for that slot.
        rare_table=None,
        wildcard_table=None,
        foil_table=None,

        token_count=1,

        # Bonus sheet behavior:
        #  - bonus_chance == 1.0  → add a bonus card (e.g., WOE's WOT)
        #  - 0 < bonus_chance < 1 → replace FIRST common with a bonus card
        bonus_chance=0.0,
        bonus_sheet_code=None,
        bonus_sheet_weights=None,
        # Optional CN range restriction for the bonus sheet:
        bonus_sheet_cn_range=None,  # e.g. (119, 128)

        # Hooks: array of {"name": str, "params": dict}
        hooks=[],

        # MH3-style foil fetchland mini-lottery (kept for your MH3)
        foil_fetchlands=False,
        foil_fetch_chance=0.057,
    ),
}

# -----------------------------
# SET ENTRIES
# -----------------------------

# FIN (Bloomburrow)
REGISTRY["fin"] = {
    **REGISTRY["_default"],
    "set_code": "fin",

    # 6–7 commons: we always draw 6 commons; FCA can REPLACE one common in 1/3 of packs
    "common_slots": 6,
    "uncommon_slots": 3,

    # FCA bonus replaces a common (1/3 chance), with the given rarity split
    "bonus_chance": 1/3,
    "bonus_sheet_code": "fca",
    "bonus_sheet_weights": {"uncommon": 63.25, "rare": 29.75, "mythic": 7.0},

    # Uncommon special (0.3%) hook: woodblock or character uncommon
    "hooks": [
        {"name": "fin_uncommon_specials", "params": {"chance": 0.003}}
    ],

    # --- Rare/Mythic slot (non-foil) ---
    # Using your split + explicit tables for alternates
    "rare_table": [
        # default frame (main set)
        {"weight": 80.0, "treatment": "regular", "query": "set:fin is:booster r:rare"},
        {"weight": 10.0, "treatment": "regular", "query": "set:fin is:booster r:mythic"},

        # borderless (cn 328–406)
        {"weight": 8.0, "treatment": "borderless", "query": "set:fin cn>=328 cn<=406 r:rare"},
        {"weight": 1.0, "treatment": "borderless", "query": "set:fin cn>=328 cn<=406 r:mythic"},

        # FF artist borderless (cn 315–323 + cn:577)
        {"weight": 0.5, "treatment": "ff artist borderless", "query": "(set:fin cn>=315 cn<=323 r:rare)"}, #since 577 is mythic only
        {"weight": 0.5, "treatment": "ff artist borderless", "query": "(set:fin cn>=315 cn<=323 r:mythic) OR (set:fin cn:577 r:mythic)"},
    ],

    # --- Wildcard slot ---
    "wildcard_table": [
        # main set
        {"weight": 16.7, "treatment": "regular", "query": "set:fin is:booster r:common"},
        {"weight": 58.3, "treatment": "regular", "query": "set:fin is:booster r:uncommon"},

        # borderless woodblock common (2.6%)
        {"weight": 2.6,  "treatment": "borderless woodblock", "query": "set:fin cn>=323 cn<=373 r:common"},

        # borderless woodblock or character uncommon (5.7% total)
        # Borderless woodblock uncommon (cn 323–373)
        {"weight": 2.85, "treatment": "woodblock", "query": "set:fin cn>=323 cn<=373 r:uncommon"},

        # Borderless character uncommon (cn 374–405)
        {"weight": 2.85, "treatment": "character", "query": "set:fin cn>=374 cn<=405 r:uncommon"},


        # rare/mythic (16.7%) — split ~80/20 like rare slot (best effort)
        {"weight": 13.36, "treatment": "regular", "query": "set:fin is:booster r:rare"},
        {"weight": 3.34,  "treatment": "regular", "query": "set:fin is:booster r:mythic"},
    ],

    # --- Foil slot (use foil prices) ---
    "foil_table": [
        # default frame foils
        {"weight": 55.75, "treatment": "regular", "query": "set:fin is:booster is:foil r:common",   "foil": True},
        {"weight": 35.90, "treatment": "regular", "query": "set:fin is:booster is:foil r:uncommon", "foil": True},
        {"weight": 5.50,  "treatment": "regular", "query": "set:fin is:booster is:foil r:rare",     "foil": True},
        {"weight": 0.25,  "treatment": "regular", "query": "set:fin is:booster is:foil r:mythic",   "foil": True},

        # booster-fun foils (borderless woodblock/character buckets)
        {"weight": 0.10, "treatment": "booster fun", "query": "set:fin is:foil cn>=323 cn<=406 r:common",   "foil": True},
        {"weight": 0.50, "treatment": "booster fun", "query": "set:fin is:foil cn>=323 cn<=406 r:uncommon", "foil": True},
        {"weight": 1.00, "treatment": "booster fun", "query": "set:fin is:foil cn>=323 cn<=406 r:rare",     "foil": True},
        {"weight": 0.25, "treatment": "booster fun", "query": "set:fin is:foil cn>=323 cn<=406 r:mythic",   "foil": True},

        # 1 of 15 Cid variants (foil)
        {"weight": 0.25, "treatment": "cid variant", "query": "(set:fin is:foil cn>=407 cn<=420) OR (set:fin is:foil cn:216)", "foil": True},
    ],
}



# Tarkir Booster
REGISTRY["tdm"] = {
    **REGISTRY["_default"],
    "set_code": "tdm",

    # 6–7 commons (we draw 6; the bonus sheet can replace 1 common)
    "common_slots": 6,
    "uncommon_slots": 3,

    # SPG replaces one common 1.5% of the time (only SPG #104–113)
    "bonus_chance": 0.015,
    "bonus_sheet_code": "spg",
    "bonus_sheet_cn_range": (104, 113),

    # ---- Rare/Mythic slot ----
    "rare_table": [
        # Main set
        {"weight": 75.0,  "treatment": "regular",                "query": "set:tdm is:booster r:rare"},
        {"weight": 12.5,  "treatment": "regular",                "query": "set:tdm is:booster r:mythic"},

        # Showcase draconic frame (cn 292–326)
        {"weight": 0.8,   "treatment": "showcase draconic",      "query": "set:tdm cn>=292 cn<=326 r:rare"},
        {"weight": 0.6,   "treatment": "showcase draconic",      "query": "set:tdm cn>=292 cn<=326 r:mythic"},

        # Borderless clan cards (cn 327–376)
        {"weight": 6.4,   "treatment": "borderless clan",        "query": "set:tdm cn>=327 cn<=376 r:rare"},
        {"weight": 1.2,   "treatment": "borderless clan",        "query": "set:tdm cn>=327 cn<=376 r:mythic"},

        # Borderless sagas/sieges/lands + (borderless) Elspeth, Storm Slayer (cn 383–398)
        {"weight": 2.7,   "treatment": "borderless saga/siege/land", "query": "set:tdm cn>=383 cn<=398 r:rare"},
        {"weight": 0.1,   "treatment": "borderless saga/siege/land", "query": "set:tdm cn>=383 cn<=398 r:mythic"},

        # Borderless reversible dragon (cn 377–382)
        {"weight": 0.8,   "treatment": "borderless reversible dragon", "query": "set:tdm cn>=377 cn<=382 r:rare"},
        {"weight": 0.9,   "treatment": "borderless reversible dragon", "query": "set:tdm cn>=377 cn<=382 r:mythic"},
    ],

    # ---- Wildcard slot ----
    "wildcard_table": [
        # Main set
        {"weight": 12.5,  "treatment": "regular",                "query": "set:tdm is:booster r:common"},
        {"weight": 58.3,  "treatment": "regular",                "query": "set:tdm is:booster r:uncommon"},
        {"weight": 15.6,  "treatment": "regular",                "query": "set:tdm is:booster r:rare"},
        {"weight": 2.5,   "treatment": "regular",                "query": "set:tdm is:booster r:mythic"},

        # Showcase draconic frame (cn 292–326)
        {"weight": 4.6,   "treatment": "showcase draconic",      "query": "set:tdm cn>=292 cn<=326 r:common"},
        {"weight": 3.8,   "treatment": "showcase draconic",      "query": "set:tdm cn>=292 cn<=326 r:uncommon"},

        # Borderless clan cards (cn 327–376)
        {"weight": 1.3,   "treatment": "borderless clan",        "query": "set:tdm cn>=327 cn<=376 r:rare"},
        {"weight": 0.2,   "treatment": "borderless clan",        "query": "set:tdm cn>=327 cn<=376 r:mythic"},

        # Borderless sagas/sieges/lands + Elspeth (cn 383–398)
        {"weight": 0.6,   "treatment": "borderless saga/siege/land", "query": "set:tdm cn>=383 cn<=398 r:rare"},
        {"weight": 0.1,   "treatment": "borderless saga/siege/land", "query": "set:tdm cn>=383 cn<=398 r:mythic"},

        # Borderless reversible dragon (cn 377–382)
        {"weight": 0.2,   "treatment": "borderless reversible dragon", "query": "set:tdm cn>=377 cn<=382 r:rare"},
        {"weight": 0.1,   "treatment": "borderless reversible dragon", "query": "set:tdm cn>=377 cn<=382 r:mythic"},
    ],

    # ---- Foil slot (use foil prices) ----
    "foil_table": [
        # Main set foils
        {"weight": 56.5,  "treatment": "regular",                "query": "set:tdm is:booster is:foil r:common",   "foil": True},
        {"weight": 32.0,  "treatment": "regular",                "query": "set:tdm is:booster is:foil r:uncommon", "foil": True},
        {"weight": 6.4,   "treatment": "regular",                "query": "set:tdm is:booster is:foil r:rare",     "foil": True},
        {"weight": 1.1,   "treatment": "regular",                "query": "set:tdm is:booster is:foil r:mythic",   "foil": True},

        # Showcase draconic frame foils (cn 292–326)
        {"weight": 1.6,   "treatment": "showcase draconic",      "query": "set:tdm is:foil cn>=292 cn<=326 r:common",   "foil": True},
        {"weight": 1.4,   "treatment": "showcase draconic",      "query": "set:tdm is:foil cn>=292 cn<=326 r:uncommon", "foil": True},
        {"weight": 0.9,   "treatment": "showcase draconic",      "query": "set:tdm is:foil cn>=292 cn<=326 r:rare",     "foil": True},
        {"weight": 0.1,   "treatment": "showcase draconic",      "query": "set:tdm is:foil cn>=292 cn<=326 r:mythic",   "foil": True},

        # Borderless clan foils (cn 327–376)
        {"weight": 0.5,   "treatment": "borderless clan",        "query": "set:tdm is:foil cn>=327 cn<=376 r:rare",     "foil": True},
        {"weight": 0.1,   "treatment": "borderless clan",        "query": "set:tdm is:foil cn>=327 cn<=376 r:mythic",   "foil": True},

        # Borderless sagas/sieges/lands + Elspeth foils (cn 383–398)
        {"weight": 0.2,   "treatment": "borderless saga/siege/land", "query": "set:tdm is:foil cn>=383 cn<=398 r:rare",   "foil": True},
        {"weight": 0.1,   "treatment": "borderless saga/siege/land", "query": "set:tdm is:foil cn>=383 cn<=398 r:mythic", "foil": True},

        # Borderless reversible dragon foils (cn 377–382)
        {"weight": 0.05,   "treatment": "borderless reversible dragon", "query": "set:tdm is:foil cn>=377 cn<=382 r:rare",   "foil": True},
        {"weight": 0.05,   "treatment": "borderless reversible dragon", "query": "set:tdm is:foil cn>=377 cn<=382 r:mythic", "foil": True},
    ],
}


# DFT
# --- DFT: Aetherdrift (Play Booster) ---
REGISTRY["dft"] = {
    **REGISTRY["_default"],
    "set_code": "dft",

    # 6–7 commons (draw 6; SPG may replace 1 common)
    "common_slots": 7,
    "uncommon_slots": 3,

    # Special Guests: 1.5% of boosters replace one common; only SPG #84–93
    "bonus_chance": 0.015,
    "bonus_sheet_code": "spg",
    "bonus_sheet_cn_range": (84, 93),

    # ---- Rare/Mythic slot ----
    # 60 rares (78%), 20 mythics (13%) main set
    # 45 borderless rares (8%), 13 borderless mythics (1%)
    # Borderless themes:
    #   Revved Up = cn 292–332
    #   Rude Riders = cn 333–346
    "rare_table": [
        # Main set regular frame
        {"weight": 78.0, "treatment": "regular", "query": "set:dft is:booster r:rare"},
        {"weight": 13.0, "treatment": "regular", "query": "set:dft is:booster r:mythic"},

        # Borderless R/M split: 8% rare, 1% mythic — split evenly across the two themes
        # Revved Up (cn 292–332)
        {"weight": 4.0,  "treatment": "borderless revved up",  "query": "set:dft is:borderless cn>=292 cn<=332 r:rare"},
        {"weight": 0.5,  "treatment": "borderless revved up",  "query": "set:dft is:borderless cn>=292 cn<=332 r:mythic"},

        # Rude Riders (cn 333–346)
        {"weight": 4.0,  "treatment": "borderless rude riders","query": "set:dft is:borderless cn>=333 cn<=346 r:rare"},
        {"weight": 0.5,  "treatment": "borderless rude riders","query": "set:dft is:borderless cn>=333 cn<=346 r:mythic"},
        
        {"weight": 2.0, "treatment": "borderless", "query": "set:dft is:borderless cn>=355 cn<=375"}
    ],

    # ---- Wildcard slot ----
    # common 8.3%, uncommon 62.5%,
    # rare+mythic 20.8% split with SAME proportions as the rare slot (78/13 across R/M):
    # → rare ≈ 17.83%, mythic ≈ 2.97%
    # plus 8.3% borderless revved up C/U (cn 292–332)
    "wildcard_table": [
        {"weight": 8.3,   "treatment": "regular",                "query": "set:dft is:booster r:common"},
        {"weight": 62.5,  "treatment": "regular",                "query": "set:dft is:booster r:uncommon"},
        {"weight": 17.83, "treatment": "regular",                "query": "set:dft is:booster r:rare"},
        {"weight": 2.97,  "treatment": "regular",                "query": "set:dft is:booster r:mythic"},

        # Borderless revved up common/uncommon (8.3% total)
        {"weight": 4.15,  "treatment": "borderless revved up",   "query": "set:dft cn>=292 cn<=332 r:common"},
        {"weight": 4.15,  "treatment": "borderless revved up",   "query": "set:dft cn>=292 cn<=332 r:uncommon"},
    ],

    # ---- Foil slot (use foil prices) ----
    # Main set foils:
    #   Common 60.5%, Uncommon 30.0%, Rare 6.4%, Mythic 1.1%
    # Borderless foils (all themes together):
    #   Common 0.5%, Uncommon 0.5%, Rare 0.9%, Mythic 0.1%
    "foil_table": [
        # Main set foils
        {"weight": 60.5, "treatment": "regular", "query": "set:dft is:booster is:foil r:common",   "foil": True},
        {"weight": 30.0, "treatment": "regular", "query": "set:dft is:booster is:foil r:uncommon", "foil": True},
        {"weight": 6.4, "treatment": "regular", "query": "set:dft is:booster is:foil r:rare",     "foil": True},
        {"weight": 1.1, "treatment": "regular", "query": "set:dft is:booster is:foil r:mythic",   "foil": True},

        # Borderless foils (combine Revved Up + Rude Riders: cn 292–346)
        {"weight": 0.5,  "treatment": "borderless", "query": "set:dft is:foil is:borderless cn>=292 cn<=346 r:common",   "foil": True},
        {"weight": 0.5,  "treatment": "borderless", "query": "set:dft is:foil is:borderless cn>=292 cn<=346 r:uncommon", "foil": True},
        {"weight": 0.9,  "treatment": "borderless", "query": "set:dft is:foil is:borderless cn>=292 cn<=346 r:rare",     "foil": True},
        {"weight": 0.1,  "treatment": "borderless", "query": "set:dft is:foil is:borderless cn>=292 cn<=346 r:mythic",   "foil": True},
    ],

    # Land/token text is informational for now (your CLI prints token count only)
    "token_count": 1,
}

# FDN — SPG replaces a common; wildcard=foil distribution per your notes

REGISTRY["fdn"] = {
    **REGISTRY["_default"],
    "set_code": "fdn",
    
    # 6-7 commons
    "common_slots": 7,
    "uncommon_slots": 3,
    
    # special guests
    "bonus_chance": 0.015,
    "bonus_sheet_code": "spg",
    "bonus_sheet_cn_range": (74, 83),
    
    "rare_table":[
        #rare or myhthic
        {"weight": 78,   "treatment": "regular",    "query": "set:fdn is:booster r:rare"},
        {"weight": 12.8, "treatment": "regular",    "query": "set:fdn is:booster r:mythic"},
        {"weight": 7.7,  "treatment": "borderless", "query": "set:fdn is:borderless r:r"},
        {"weight": 1.5,  "treatment": "borderless", "query": "set:fdn is:borderless r:m"},
    ],
    
    "wildcard_table":[
        # traditional non-foil weight
        {"weight": 16.7,  "treatment": "regular",   "query": "set:fdn is:booster r:common"},
        {"weight": 58.3,  "treatment": "regular",   "query": "set:fdn is:booster r:uncommon"},
        {"weight": 16.3,  "treatment": "regular",   "query": "set:fdn is:booster r:rare"},
        {"weight": 2.6,   "treatment": "regular",   "query": "set:fdn is:booster r:mythic"},
        
        # borderless cards, common, uncommon, 
        {"weight": 1.8,  "treatment": "borderless", "query": "set:fdn is:borderless r:c"},
        {"weight": 2.4,  "treatment": "borderless", "query": "set:fdn is:borderless r:u"},
        {"weight": 1.6,  "treatment": "borderless", "query": "set:fdn is:borderless r:r"},
        {"weight": 0.3,  "treatment": "borderless", "query": "set:fdn is:borderless r:m"},  
    ],

    #finish u the foils
    "foil_table":[
        # same weight for traditional foils as wildcard non-foils
        {"weight": 16.7,  "treatment": "regular",   "query": "set:fdn is:booster is:foil r:common"},
        {"weight": 58.3,  "treatment": "regular",   "query": "set:fdn is:booster is:foil r:uncommon"},
        {"weight": 16.3,  "treatment": "regular",   "query": "set:fdn is:booster is:foil r:rare"},
        {"weight": 2.6,   "treatment": "regular",   "query": "set:fdn is:booster is:foil r:mythic"},
        
    ],
    
    "token count": 1,
}



# WOE — Enchanting Tales (WOT) bonus card is ADDED (not a replacement)
REGISTRY["woe"] = {
    **REGISTRY["_default"],
    "set_code": "woe",
    "common_slots": 3,
    "uncommon_slots": 3,
    "rare_weights": {"rare": 0.87, "mythic": 0.13},
    "wildcard_weights": {"common": 0.55, "uncommon": 0.30, "rare": 0.13, "mythic": 0.02},
    "foil_weights": {"common": 0.65, "uncommon": 0.25, "rare": 0.08, "mythic": 0.02},
    "bonus_chance": 1.0,
    "bonus_sheet_code": "wot",
    "bonus_sheet_weights": {"uncommon": 0.2857, "rare": 0.4762, "mythic": 0.2381},
}

# LTR — base split
REGISTRY["ltr"] = {
    **REGISTRY["_default"],
    "set_code": "ltr",
    "common_slots": 3,
    "uncommon_slots": 3,
    "rare_weights": {"rare": 0.875, "mythic": 0.125},
}

# DSK — Lurking Evil / Paranormal Frame via hook + params
REGISTRY["dsk"] = {
    **REGISTRY["_default"],
    "set_code": "dsk",
    "rare_weights": {"rare": 0.857, "mythic": 0.143},  # collapsed from subpools
    "bonus_chance": 1/64,    # Special Guest replaces a common
    "bonus_sheet_code": "spg",
    "hooks": ["dsk_lurking"],
    "lurking_evil": {
        "common_chance": 0.25,
        "uncommon_le_chance": 0.25,
        "uncommon_pf_chance": 0.25,
        "pf_uncommon_numbers": ["306","309","314","319"],
        "cn": LURKING_EVIL_COLLECTOR_NUMBERS,
    },
}

# CLB — specialty adds via hook
REGISTRY["clb"] = {
    **REGISTRY["_default"],
    "set_code": "clb",
    "rare_weights": {"rare": 0.875, "mythic": 0.125},
    "hooks": [
        {
            "name": "clb_specials",
            "params": {
                "foil_etched_legendary_bg": {
                    "enabled": True, "frequency": 1/3,
                    "rarities": {"rare": 1 - MYTHIC_CHANCE, "mythic": MYTHIC_CHANCE}
                },
                "legendary_creature_pw": {
                    "enabled": True, "frequency": 0.50,
                    "rarities": {"rare": 1 - MYTHIC_CHANCE, "mythic": MYTHIC_CHANCE}
                },
                "legendary_background": {
                    "enabled": True, "frequency": 1/12,
                    "rarities": {"rare": 1.0}
                }
            }
        }
    ],
}

# OTJ — Breaking News (OTP), Big Score (BIG)
REGISTRY["otj"] = {
    **REGISTRY["_default"],
    "set_code": "otj",
    "rare_weights": {"rare": 0.895, "mythic": 0.105},
    "wildcard_weights": {"common": 0.50, "uncommon": 0.4167, "rare": 0.0667, "mythic": 0.0166},
    "hooks": [
        {
            "name": "otj_breaking_news",
            "params": {
                "otp_sheet_code": "otp",
                "otp_odds": {"uncommon": 0.667, "rare": 0.285, "mythic": 0.048},
                # "mode": "replace_common"
            }
        }
    ],
}

# MH3 — optional foil fetchland lotto
REGISTRY["mh3"] = {
    **REGISTRY["_default"],
    "set_code": "mh3",
    "rare_weights": {"rare": 0.875, "mythic": 0.125},
    "foil_fetchlands": True,
    "foil_fetch_chance": 0.057,
    "fetchland_names": FETCHLAND_NAMES,
    "bonus_chance": 0.0,
    "bonus_sheet_code": None,
}

# EOE — Edge of Eternities (NEW)
REGISTRY["eoe"] = {
    **REGISTRY["_default"],
    "set_code": "eoe",

    # 6 commons, 3 uncommons
    "common_slots": 6,
    "uncommon_slots": 3,

    # Special Guests: (set:spg cn:119–128) — 1.8% chance replaces a common
    "bonus_chance": 0.018,
    "bonus_sheet_code": "spg",
    "bonus_sheet_cn_range": (119, 128),

    # Rare/Mythic slot table
    "rare_table": [
        # Main set R/M (regular frame)
        {"weight": 80.4, "treatment": "regular", "query": "set:eoe is:booster r:rare"},
        {"weight": 14.2, "treatment": "regular", "query": "set:eoe is:booster r:mythic"},

        # Borderless Triumphant (cn 307–316)
        {"weight": 2.0, "treatment": "borderless triumphant", "query": "set:eoe is:borderless -is:showcase -t:basic cn>=307 cn<=316 r:rare"},
        {"weight": 0.9, "treatment": "borderless triumphant", "query": "set:eoe is:borderless -is:showcase -t:basic cn>=307 cn<=316 r:mythic"},

        # Surreal Space (cn 287–302)
        {"weight": 2.0, "treatment": "borderless surreal space", "query": "set:eoe is:borderless -is:showcase -t:basic cn>=287 cn<=302 r:rare"},
        {"weight": 0.9, "treatment": "borderless surreal space", "query": "set:eoe is:borderless -is:showcase -t:basic cn>=287 cn<=302 r:mythic"},
    ],

    # Wildcard slot table
    "wildcard_table": [
        # Regular frame (main set)
        {"weight": 12.5, "treatment": "regular", "query": "set:eoe is:booster r:common"},
        {"weight": 62.5, "treatment": "regular", "query": "set:eoe is:booster r:uncommon"},
        {"weight": 10.6, "treatment": "regular", "query": "set:eoe is:booster r:rare"},
        {"weight": 0.9,  "treatment": "regular", "query": "set:eoe is:booster r:mythic"},

        # Stellar Sights land (EOS)
        {"weight": 10.0, "treatment": "stellar sights land", "query": "set:eos r:rare t:land"},
        {"weight": 2.5,  "treatment": "stellar sights land", "query": "set:eos r:mythic t:land"},

        # Borderless viewport land (exclude Secluded Starforge cn:366)
        {"weight": 1.0, "treatment": "borderless viewport land", "query": "set:eoe is:showcase t:land -cn:366 r:rare"},
        {"weight": 0.9, "treatment": "borderless viewport land", "query": "set:eoe is:showcase t:land -cn:366 r:mythic"},

        # Borderless Triumphant (cn 307–316)
        {"weight": 1.0, "treatment": "borderless triumphant", "query": "set:eoe is:borderless -is:showcase -t:basic cn>=307 cn<=316 r:rare"},
        {"weight": 0.9, "treatment": "borderless triumphant", "query": "set:eoe is:borderless -is:showcase -t:basic cn>=307 cn<=316 r:mythic"},

        # Borderless Surreal Space (cn 287–302)
        {"weight": 1.0, "treatment": "borderless surreal space", "query": "set:eoe is:borderless -is:showcase -t:basic cn>=287 cn<=302 r:rare"},
        {"weight": 0.9, "treatment": "borderless surreal space", "query": "set:eoe is:borderless -is:showcase -t:basic cn>=287 cn<=302 r:mythic"},
    ],

    # Foil slot table — use foil prices (we fetch with is:foil)
    "foil_table": [
        # Main set (regular frame, booster legal)
        {"weight": 58.0, "treatment": "regular", "query": "set:eoe is:booster is:foil r:common",  "foil": True},
        {"weight": 32.0, "treatment": "regular", "query": "set:eoe is:booster is:foil r:uncommon","foil": True},
        {"weight": 6.4,  "treatment": "regular", "query": "set:eoe is:booster is:foil r:rare",    "foil": True},
        {"weight": 1.1,  "treatment": "regular", "query": "set:eoe is:booster is:foil r:mythic",  "foil": True},

        # Stellar Sights land (EOS)
        {"weight": 1.0, "treatment": "stellar sights land", "query": "set:eos is:foil r:rare",   "foil": True},
        {"weight": 0.9, "treatment": "stellar sights land", "query": "set:eos is:foil r:mythic", "foil": True},

        # Borderless viewport / triumphant / surreal space (EOE alternates)
        # viewport: showcase lands (exclude cn:366)
        {"weight": 0.9, "treatment": "borderless viewport land", "query": "set:eoe is:foil is:showcase t:land -cn:366 r:rare",   "foil": True},
        {"weight": 0.9, "treatment": "borderless viewport land", "query": "set:eoe is:foil is:showcase t:land -cn:366 r:mythic", "foil": True},

        # triumphant (cn 307–316)
        {"weight": 0.9, "treatment": "borderless triumphant", "query": "set:eoe is:foil is:borderless -is:showcase -t:basic cn>=307 cn<=316 r:rare",   "foil": True},
        {"weight": 0.9, "treatment": "borderless triumphant", "query": "set:eoe is:foil is:borderless -is:showcase -t:basic cn>=307 cn<=316 r:mythic", "foil": True},

        # surreal space (cn 287–302)
        {"weight": 0.9, "treatment": "borderless surreal space", "query": "set:eoe is:foil is:borderless -is:showcase -t:basic cn>=287 cn<=302 r:rare",   "foil": True},
        {"weight": 0.9, "treatment": "borderless surreal space", "query": "set:eoe is:foil is:borderless -is:showcase -t:basic cn>=287 cn<=302 r:mythic", "foil": True},
    ],
}
