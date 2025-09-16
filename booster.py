# booster.py — unified opener driven by booster_registry.REGISTRY (query-driven, readable)

import requests, random, time  # type: ignore
from typing import Dict, Any, Callable, Optional, List, Tuple

from booster_registry import REGISTRY, FETCHLAND_NAMES

# =========================
# Utilities
# =========================

def pick_weighted(weights: Dict[str, float]) -> str:
    keys, vals = zip(*weights.items())
    return random.choices(keys, weights=vals, k=1)[0]

def pick_from_table(table: List[Dict[str, Any]]) -> Dict[str, Any]:
    weights = [entry.get("weight", 1.0) for entry in table]
    idx = random.choices(range(len(table)), weights=weights, k=1)[0]
    return table[idx]

def color_emojis(card: Dict[str, Any]) -> str:
    # Use color_identity; fallback to produced mana or type heuristics
    mapping = {"W": "⚪", "U": "🔵", "B": "⚫", "R": "🔴", "G": "🟢"}
    colorIdentity = card.get("color_identity") or []
    if not colorIdentity:
        typeline = (card.get("type_line") or "").lower()
        if "land" in typeline and "basic" in typeline and "wastes" not in typeline:
            # basic lands: guess by name if no color identity (rare, but safe fallback)
            name = (card.get("name") or "").lower()
            if "plains" in name: colorIdentity = ["W"]
            elif "island" in name: colorIdentity = ["U"]
            elif "swamp" in name: colorIdentity = ["B"]
            elif "mountain" in name: colorIdentity = ["R"]
            elif "forest" in name: colorIdentity = ["G"]
        # still empty → colorless
    if not colorIdentity:
        return "⚙️"
    return "".join(mapping.get(c, "⚙️") for c in colorIdentity)

def _is_legendary(card: dict) -> bool:
    if not card: return False
    if "is_legendary" in card: return bool(card["is_legendary"])
    tl = (card.get("type_line") or "").lower()
    if "legendary" in tl: return True
    sup = card.get("supertypes") or []
    return any(str(s).lower() == "legendary" for s in sup)

# =========================
# Fetch helpers (now support raw Scryfall query)
# =========================

def fetch_random_card(
    set_code: Optional[str] = None,
    rarity: Optional[str] = None,
    is_foil: bool = False,
    variation: bool = False,
    frame: Optional[str] = None,
    type_line: Optional[str] = None,
    set_override: Optional[str] = None,
    collector_number: Optional[str] = None,
    produces: Optional[str] = None,
    full_art: bool = False,
    raw_query: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Single random card from Scryfall with flexible filters.
    If raw_query is provided, it is used verbatim (plus our global -!"Ragnarok, Divine Deliverance").
    """
    if raw_query:
        query = raw_query.strip()
        if '-!"Ragnarok, Divine Deliverance"' not in query:
            query += ' -!"Ragnarok, Divine Deliverance"'
        url = "https://api.scryfall.com/cards/random?q=" + "+".join(query.split())
    else:
        query: List[str] = []
        actual_set = set_override or set_code
        if actual_set:
            query.append(f"set:{actual_set}")

        exempt_sets = {"spg","fca","eos","otp","big","wot","mul","brc","dmc","sta","zne"}

        if type_line == "basic land":
            query.append("t:basic")
        elif actual_set not in exempt_sets and type_line != "token":
            query.append("is:booster")

        if rarity: query.append(f"rarity:{rarity}")
        if is_foil: query.append("is:foil")
        if variation: query.append("variation:true")
        if frame: query.append(f"frame:{frame}")
        if type_line and type_line != "basic land": query.append(f"type:{type_line}")
        if full_art: query.append("t:full_art")
        if collector_number: query.append(f"cn:{collector_number}")
        if produces: query.append(f"produces:{produces}")

        query.append('-!"Ragnarok, Divine Deliverance"')
        url = "https://api.scryfall.com/cards/random?q=" + "+".join(query)

    try:
        req = requests.get(url, timeout=20)
        req.raise_for_status()
        return req.json()
    except requests.RequestException as err:
        print("[fetch_random_card] Error:", err, "| URL:", url)
        return None

def fetch_bonus_sheet_card(cfg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    sheet = cfg.get("bonus_sheet_code")
    weights = cfg.get("bonus_sheet_weights")
    bonusSheetCollectorNumRange: Optional[Tuple[int,int]] = cfg.get("bonus_sheet_cn_range")
    # Try a few times to hit the CN restriction if present
    for _ in range(12):
        rarity = pick_weighted(weights) if weights else None
        card = fetch_random_card(set_override=sheet, rarity=rarity)
        if not card: continue
        if not bonusSheetCollectorNumRange:
            return card
        collectorNumString = (card.get("collector_number") or "").split("★")[0]  # handle star variants safely
        try:
            collectorNum = int(collectorNumString)
            if bonusSheetCollectorNumRange[0] <= collectorNum <= bonusSheetCollectorNumRange[1]:
                return card
        except:
            pass
    return None

# =========================
# Hooks (DSK / OTJ / CLB / FIN)
# =========================

def dsk_lurking_hook(slot_name: str, set_code: dict, params: Optional[dict] = None):
    if set_code.get("set_code") != "dsk": 
        return None
    lurkingEvil = (params or set_code.get("lurking_evil") or {}).copy()
    collectorNum = (lurkingEvil.get("cn") or {}).copy()

    if slot_name == "common":
        if random.random() < lurkingEvil.get("common_chance", 0.0):
            num = random.choice(collectorNum.get("common", []))
            if num:
                return fetch_random_card("dsk", "common", collector_number=num)

    if slot_name == "uncommon":
        r = random.random()
        le_p = lurkingEvil.get("uncommon_le_chance", 0.0)
        pf_p = lurkingEvil.get("uncommon_pf_chance", 0.0)
        if r < le_p:
            num = random.choice(collectorNum.get("uncommon", []))
            if num:
                return fetch_random_card("dsk", "uncommon", collector_number=num)
        elif r < le_p + pf_p:
            num = random.choice(lurkingEvil.get("pf_uncommon_numbers", []))
            if num:
                return fetch_random_card("dsk", "uncommon", collector_number=num)
    return None

def otj_breaking_news_hook(slot_name: str, set_code: dict, params: Optional[dict] = None):
    if set_code.get("set_code") != "otj": 
        return None
    if slot_name != "post": 
        return None
    p = params or {}
    odds = p.get("otp_odds", {"uncommon": 0.667, "rare": 0.285, "mythic": 0.048})
    sheet = p.get("otp_sheet_code", "otp")
    rarity = pick_weighted(odds)
    card = fetch_random_card(set_override=sheet, rarity=rarity)
    return [card] if card else None

def clb_specials_hook(slot_name: str, set_code: dict, params: Optional[dict] = None):
    if set_code.get("set_code") != "clb": 
        return None
    if slot_name != "post": 
        return None
    p = params or {}
    hookOut: List[Dict[str,Any]] = []

    def maybe_add(item: dict):
        if not item or not item.get("enabled", True): 
            return
        freq = item.get("frequency", 0.0)
        if random.random() <= freq:
            rarity = pick_weighted(item.get("rarities", {"rare": 1.0}))
            bonusSheetCode = item.get("sheet_code") or "clb"
            card = fetch_random_card(set_override=bonusSheetCode, rarity=rarity)
            if card: hookOut.append(card)

    maybe_add(p.get("foil_etched_legendary_bg"))
    maybe_add(p.get("legendary_creature_pw"))
    maybe_add(p.get("legendary_background"))

    return hookOut or None

def fin_uncommon_specials_hook(slot_name: str, set_code: dict, params: Optional[dict] = None):
    """FIN: 0.3% chance an uncommon is a borderless woodblock or character card."""
    if set_code.get("set_code") != "fin" or slot_name != "uncommon":
        return None
    p = params or {}
    chance = p.get("chance", 0.003)  # 0.3% per uncommon slot
    if random.random() >= chance:
        return None

    # 50/50 woodblock vs character unless we change it in params
    mode = random.choice(["woodblock", "character"])
    if mode == "woodblock":
        query = "set:fin cn>=323 cn<=373 r:uncommon"
        treatment = "borderless woodblock"
    else:
        query = "set:fin cn>=374 cn<=405 r:uncommon"
        treatment = "borderless character"

    card = fetch_random_card(raw_query=query)
    if card:
        card["x_treatment"] = treatment
    return card



# =========================
# Display helpers
# =========================

def display_card(card: Optional[Dict[str,Any]], is_foil=False) -> float:
    if not card: return 0.0
    name = card.get("name","Unknown")
    rarity = card.get("rarity","unknown")
    treatment = (card.get("x_treatment") or "").strip().lower()
    colors = color_emojis(card)

    prices = card.get("prices",{})
    key = "eur_foil" if is_foil else "eur"
    value = prices.get(key) or prices.get("usd_foil" if is_foil else "usd")

    # Build prefix like: (rare) (borderless triumphant) (FOIL) 🟢🔴 Name 0.00 €
    parts = [f"({rarity})"]
    #  Only include treatment if it’s NON-regular
    if treatment != "regular":
        parts.append(f"({treatment})")
    if is_foil:
        parts.append("(FOIL)")
    parts.append(colors)
    head = " ".join(parts)

    price_str = f"{value} €" if value else "N/A"
    print(f"{head} {name} {price_str}")

    try:
        return float(value) if value else 0.0
    except:
        return 0.0


def display_booster(booster, foil, bonus, token_count, suspense=True):
    print("\nYour Booster Pack:\n")
    total = 0.0
    for i, card in enumerate(booster, 1):
        print(f"{i:02}. ", end="")#waits 2 seccpnds
        total += display_card(card)
        if suspense: time.sleep(3 if card and card.get("rarity") in {"rare","mythic"} else 2)

    if foil:
        print("\n✨ Foil:")
        total += display_card(foil, is_foil=True)
        if suspense: time.sleep(2)

    if bonus:
        print("\n📜 Bonus Sheet:")
        total += display_card(bonus)
        if suspense: time.sleep(2)

    print(f"\n🎟️ Tokens/Art Cards: {token_count}")
    print(f"💰 Total Pack Value: {total:.2f}€")

# =========================
# Core opener 
# =========================

def _resolve_hooks(cfg: dict):
    name_to_callable = {
        "dsk_lurking": dsk_lurking_hook,
        "otj_breaking_news": otj_breaking_news_hook,
        "clb_specials": clb_specials_hook,
        "fin_uncommon_specials": fin_uncommon_specials_hook,

    }
    resolved: List[Callable[[str, dict], Optional[Any]]] = []
    for hooks in cfg.get("hooks", []):
        if isinstance(hooks, str):
            fn = name_to_callable.get(hooks)
            if fn:
                resolved.append(lambda slot, ctx, _fn=fn: _fn(slot, ctx, None))
        elif isinstance(hooks, dict):
            name = hooks.get("name")
            params = hooks.get("params", {})
            fn = name_to_callable.get(name)
            if fn:
                resolved.append(lambda slot, ctx, _fn=fn, _p=params: _fn(slot, ctx, _p))
    return resolved

def _fetch_with_meta(query: str, treatment: Optional[str], force_foil: bool=False) -> Optional[Dict[str,Any]]:
    card = fetch_random_card(raw_query=query)
    if card:
        if treatment:
            card["x_treatment"] = treatment
    return card

def open_booster(setCode: str):
    setCode = setCode.lower()
    config = REGISTRY.get(setCode, REGISTRY["_default"]).copy()
    config["set_code"] = setCode

    hooks = _resolve_hooks(config)
    config["hooks"] = hooks

    booster: List[Dict[str,Any]] = []
    bonus_card = None

    # --- commons (with optional SPG replacement) ---
    commons_to_draw = config["common_slots"]

    if config.get("bonus_chance", 0) > 0 and config.get("bonus_sheet_code"):
        if config["bonus_chance"] >= 1.0:
            bonus_card = fetch_bonus_sheet_card(config)
        elif random.random() < config["bonus_chance"]:
            bc = fetch_bonus_sheet_card(config)
            if bc:
                bonus_card = bc
                commons_to_draw -= 1

    for _ in range(max(0, commons_to_draw)):
        # allow hook to replace a common (DSK variant, etc.)
        card = None
        for hook in hooks:
            res = hook("common", config)
            card = res or card
        booster.append(card or fetch_random_card(setCode, "common"))

    # --- uncommons ---
    for _ in range(config["uncommon_slots"]):
        card = None
        for hook in hooks:
            res = hook("uncommon", config)
            card = res or card
        booster.append(card or fetch_random_card(setCode, "uncommon"))

    # --- rare/mythic slot ---
    if config.get("rare_table"):
        entry = pick_from_table(config["rare_table"])
        card = _fetch_with_meta(entry["query"], entry.get("treatment"))
        # hooks can override if they intercept this slot
        for hook in hooks:
            override = hook("rare_slot", config)
            card = override or card
        booster.append(card)
    else:
        rareWeights = pick_weighted(config["rare_weights"])
        card = None
        for hook in hooks:
            res = hook("rare_slot", config)
            card = res or card
        booster.append(card or fetch_random_card(setCode, rareWeights))

    # --- wildcard slot ---
    if config.get("wildcard_table"):
        entry = pick_from_table(config["wildcard_table"])
        booster.append(_fetch_with_meta(entry["query"], entry.get("treatment")))
    else:
        wc = pick_weighted(config["wildcard_weights"])
        card = None
        for hook in hooks:
            res = hook("wildcard", config)
            card = res or card
        booster.append(card or fetch_random_card(setCode, wc))

    # --- foil slot (table-aware, uses foil prices) ---
    foil = None
    if config.get("foil_table"):
        entry = pick_from_table(config["foil_table"])
        foil = _fetch_with_meta(entry["query"], entry.get("treatment"), force_foil=True)
    else:
        # legacy: MH3 fetchland
        if config.get("foil_fetchlands"):
            if random.random() < config.get("foil_fetch_chance", 0.057):
                for _ in range(8):
                    cand = fetch_random_card(setCode, "rare", is_foil=True)
                    if cand and cand.get("name") in config.get("fetchland_names", FETCHLAND_NAMES):
                        foil = cand; break
        if not foil:
            foil_rarity = pick_weighted(config["foil_weights"])
            foil = fetch_random_card(setCode, foil_rarity, is_foil=True)

    # --- post-build hooks (OTP, CLB adds, etc.) ---
    for hook in hooks:
        extra = hook("post", config)
        if extra:
            if isinstance(extra, list):
                booster.extend([c for c in extra if c])
            elif isinstance(extra, dict):
                booster.append(extra)

    token_count = config.get("token_count", 1)
    return booster, foil, bonus_card, token_count

# =========================
# Tiny CLI
# =========================

def main():
    modes = {"1": "single", "2": "compare"}
    print("1. Open a single booster\n2. Compare two sets")
    mode = input("Enter 1 or 2: ").strip()
    suspense = input("Reveal one by one? (y/n): ").strip().lower() == "y"
    
    
    MTGSets = set(k for k in REGISTRY.keys() if not k.startswith("_")) | {
        "blb","mkm","lci","cmm","mom","one","bro","dmu","snc","neo","vow","mid","afr","stx","khm","znr","thb","fut",
    }

    if modes.get(mode) == "compare":
        def ask(prompt, exclude=None): # leave exclude for whenever we want to compare different boosters
            while True:
                checkSet = input(prompt).strip().lower()# strips takes all empty space out, lower makes it all lowercase
                if checkSet in MTGSets: # and checkSet != exclude: (if not comparing same set uncomment this line)
                    return checkSet
                print("Invalid set.")

        firstSet = ask("First set: ")
        secondSet = ask("Second set: ")
        rounds = input("How many boosters? (Rounds)").strip() # investigate a way to while loop this u
        totals = {firstSet: 0.0, secondSet: 0.0}

        for i in range(rounds): # rounds to make finals be 5v5 boosters
            for set_code in (firstSet, secondSet):
                print(f"\n--- {set_code.upper()} Booster #{i+1} ---")
                booster, foil, bonus, token = open_booster(set_code)
                display_booster(booster, foil, bonus, token, suspense)

                #defines the function that finds the price
                def value(i, foil=False):
                    if not i: 
                        return 0.0
                    prices = i.get("prices", {})
                    if foil:
                        eur = "eur_foil"
                    else:
                        eur = "eur"
                    finalValue = prices.get(eur) or prices.get("usd_foil" if foil else "usd")
                    try: 
                        return float(finalValue) if finalValue else 0.0
                    except: 
                        return 0.0

                totalValueOfPack = sum(value(i) for i in booster) + value(foil, True) + value(bonus)
                totals[set_code] += totalValueOfPack
                input("Press Enter...")

        print("\n=== Results ===")
        print(f"{firstSet.upper()}: {totals[firstSet]:.2f}€")
        print(f"{secondSet.upper()}: {totals[secondSet]:.2f}€")
        if totals[firstSet] > totals[secondSet]:
            print("Winner: ", firstSet)
        elif totals[firstSet] < totals[secondSet]:
            print("Winner: ", secondSet)
        else:
            print("Tie!")    
        #print("Winner:", (firstSet if totals[firstSet] > totals[secondSet] else secondSet if totals[secondSet] > totals[firstSet] else "Tie!").upper())
    else:
        set_code = input("\nSet code (eoe, tdm, dft): ").strip().lower()
        if set_code not in MTGSets:
            print("Invalid set. Load code to Try again.")
            return
        booster, foil, bonus, token = open_booster(set_code)
        display_booster(booster, foil, bonus, token, suspense)

if __name__ == "__main__":
    main()
