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
        tl = (card.get("type_line") or "").lower()
        if "land" in tl and "basic" in tl and "wastes" not in tl:
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
        q = raw_query.strip()
        if '-!"Ragnarok, Divine Deliverance"' not in q:
            q += ' -!"Ragnarok, Divine Deliverance"'
        url = "https://api.scryfall.com/cards/random?q=" + "+".join(q.split())
    else:
        q: List[str] = []
        actual_set = set_override or set_code
        if actual_set:
            q.append(f"set:{actual_set}")

        exempt_sets = {"spg","fca","eos","otp","big","wot","mul","brc","dmc","sta","zne"}

        if type_line == "basic land":
            q.append("t:basic")
        elif actual_set not in exempt_sets and type_line != "token":
            q.append("is:booster")

        if rarity: q.append(f"rarity:{rarity}")
        if is_foil: q.append("is:foil")
        if variation: q.append("variation:true")
        if frame: q.append(f"frame:{frame}")
        if type_line and type_line != "basic land": q.append(f"type:{type_line}")
        if full_art: q.append("t:full_art")
        if collector_number: q.append(f"cn:{collector_number}")
        if produces: q.append(f"produces:{produces}")

        q.append('-!"Ragnarok, Divine Deliverance"')
        url = "https://api.scryfall.com/cards/random?q=" + "+".join(q)

    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print("[fetch_random_card] Error:", e, "| URL:", url)
        return None

def fetch_bonus_sheet_card(cfg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    sheet = cfg.get("bonus_sheet_code")
    weights = cfg.get("bonus_sheet_weights")
    cn_range: Optional[Tuple[int,int]] = cfg.get("bonus_sheet_cn_range")
    # Try a few times to hit the CN restriction if present
    for _ in range(12):
        rarity = pick_weighted(weights) if weights else None
        c = fetch_random_card(set_override=sheet, rarity=rarity)
        if not c: continue
        if not cn_range:
            return c
        cn_str = (c.get("collector_number") or "").split("★")[0]  # handle star variants safely
        try:
            cn = int(cn_str)
            if cn_range[0] <= cn <= cn_range[1]:
                return c
        except:
            pass
    return None

# =========================
# Hooks (DSK / OTJ / CLB / FIN)
# =========================

def dsk_lurking_hook(slot_name: str, ctx: dict, params: Optional[dict] = None):
    if ctx.get("set_code") != "dsk": return None
    le = (params or ctx.get("lurking_evil") or {}).copy()
    cn = (le.get("cn") or {}).copy()

    if slot_name == "common":
        if random.random() < le.get("common_chance", 0.0):
            num = random.choice(cn.get("common", []))
            if num:
                return fetch_random_card("dsk", "common", collector_number=num)

    if slot_name == "uncommon":
        r = random.random()
        le_p = le.get("uncommon_le_chance", 0.0)
        pf_p = le.get("uncommon_pf_chance", 0.0)
        if r < le_p:
            num = random.choice(cn.get("uncommon", []))
            if num:
                return fetch_random_card("dsk", "uncommon", collector_number=num)
        elif r < le_p + pf_p:
            num = random.choice(le.get("pf_uncommon_numbers", []))
            if num:
                return fetch_random_card("dsk", "uncommon", collector_number=num)
    return None

def otj_breaking_news_hook(slot_name: str, ctx: dict, params: Optional[dict] = None):
    if ctx.get("set_code") != "otj": return None
    if slot_name != "post": return None
    p = params or {}
    odds = p.get("otp_odds", {"uncommon": 0.667, "rare": 0.285, "mythic": 0.048})
    sheet = p.get("otp_sheet_code", "otp")
    rarity = pick_weighted(odds)
    card = fetch_random_card(set_override=sheet, rarity=rarity)
    return [card] if card else None

def clb_specials_hook(slot_name: str, ctx: dict, params: Optional[dict] = None):
    if ctx.get("set_code") != "clb": return None
    if slot_name != "post": return None
    p = params or {}
    out: List[Dict[str,Any]] = []

    def maybe_add(item: dict):
        if not item or not item.get("enabled", True): return
        freq = item.get("frequency", 0.0)
        if random.random() <= freq:
            r = pick_weighted(item.get("rarities", {"rare": 1.0}))
            sc = item.get("sheet_code") or "clb"
            c = fetch_random_card(set_override=sc, rarity=r)
            if c: out.append(c)

    maybe_add(p.get("foil_etched_legendary_bg"))
    maybe_add(p.get("legendary_creature_pw"))
    maybe_add(p.get("legendary_background"))

    return out or None

def fin_uncommon_specials_hook(slot_name: str, ctx: dict, params: Optional[dict] = None):
    """FIN: 0.3% chance an uncommon is a borderless woodblock or character card."""
    if ctx.get("set_code") != "fin" or slot_name != "uncommon":
        return None
    p = params or {}
    chance = p.get("chance", 0.003)  # 0.3% per uncommon slot
    if random.random() >= chance:
        return None

    # 50/50 woodblock vs character unless you change it in params
    mode = random.choice(["woodblock", "character"])
    if mode == "woodblock":
        q = "set:fin cn>=323 cn<=373 r:uncommon"
        t = "borderless woodblock"
    else:
        q = "set:fin cn>=374 cn<=405 r:uncommon"
        t = "borderless character"

    c = fetch_random_card(raw_query=q)
    if c:
        c["x_treatment"] = t
    return c



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
    val = prices.get(key) or prices.get("usd_foil" if is_foil else "usd")

    # Build prefix like: (rare) (borderless triumphant) (FOIL) 🟢🔴 Name 0.00 €
    parts = [f"({rarity})"]
    # ⚠️ Only include treatment if it’s NON-regular
    if treatment and treatment != "regular":
        parts.append(f"({treatment})")
    if is_foil:
        parts.append("(FOIL)")
    parts.append(colors)
    head = " ".join(parts)

    price_str = f"{val} €" if val else "N/A"
    print(f"{head} {name} {price_str}")

    try:
        return float(val) if val else 0.0
    except:
        return 0.0


def display_booster(booster, foil, bonus, token_count, suspense=True):
    print("\nYour Booster Pack:\n")
    total = 0.0
    for i, c in enumerate(booster, 1):
        print(f"{i:02}. ", end="")
        total += display_card(c)
        if suspense: time.sleep(3 if c and c.get("rarity") in {"rare","mythic"} else 2)

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
# Core opener (now table-aware)
# =========================

def _apply_hooks(set_code, pack, rng, pools):  # placeholder if you add pools service later
    return pack

def _resolve_hooks(cfg: dict):
    name_to_callable = {
        "dsk_lurking": dsk_lurking_hook,
        "otj_breaking_news": otj_breaking_news_hook,
        "clb_specials": clb_specials_hook,
        "fin_uncommon_specials": fin_uncommon_specials_hook,  # ← add this line

    }
    resolved: List[Callable[[str, dict], Optional[Any]]] = []
    for h in cfg.get("hooks", []):
        if isinstance(h, str):
            fn = name_to_callable.get(h)
            if fn:
                resolved.append(lambda slot, ctx, _fn=fn: _fn(slot, ctx, None))
        elif isinstance(h, dict):
            name = h.get("name")
            params = h.get("params", {})
            fn = name_to_callable.get(name)
            if fn:
                resolved.append(lambda slot, ctx, _fn=fn, _p=params: _fn(slot, ctx, _p))
    return resolved

def _fetch_with_meta(query: str, treatment: Optional[str], force_foil: bool=False) -> Optional[Dict[str,Any]]:
    c = fetch_random_card(raw_query=query)
    if c:
        if treatment:
            c["x_treatment"] = treatment
    return c

def open_booster(set_code: str):
    sc = set_code.lower()
    cfg = REGISTRY.get(sc, REGISTRY["_default"]).copy()
    cfg["set_code"] = sc

    hooks = _resolve_hooks(cfg)
    cfg["hooks"] = hooks

    booster: List[Dict[str,Any]] = []
    bonus_card = None

    # --- commons (with optional SPG replacement) ---
    commons_to_draw = cfg["common_slots"]

    if cfg.get("bonus_chance", 0) > 0 and cfg.get("bonus_sheet_code"):
        if cfg["bonus_chance"] >= 1.0:
            bonus_card = fetch_bonus_sheet_card(cfg)
        elif random.random() < cfg["bonus_chance"]:
            bc = fetch_bonus_sheet_card(cfg)
            if bc:
                bonus_card = bc
                commons_to_draw -= 1

    for _ in range(max(0, commons_to_draw)):
        # allow hook to replace a common (DSK variant, etc.)
        card = None
        for hook in hooks:
            res = hook("common", cfg)
            card = res or card
        booster.append(card or fetch_random_card(sc, "common"))

    # --- uncommons ---
    for _ in range(cfg["uncommon_slots"]):
        card = None
        for hook in hooks:
            res = hook("uncommon", cfg)
            card = res or card
        booster.append(card or fetch_random_card(sc, "uncommon"))

    # --- rare/mythic slot ---
    if cfg.get("rare_table"):
        entry = pick_from_table(cfg["rare_table"])
        card = _fetch_with_meta(entry["query"], entry.get("treatment"))
        # hooks can override if they intercept this slot
        for hook in hooks:
            override = hook("rare_slot", cfg)
            card = override or card
        booster.append(card)
    else:
        rm = pick_weighted(cfg["rare_weights"])
        card = None
        for hook in hooks:
            res = hook("rare_slot", cfg)
            card = res or card
        booster.append(card or fetch_random_card(sc, rm))

    # --- wildcard slot ---
    if cfg.get("wildcard_table"):
        entry = pick_from_table(cfg["wildcard_table"])
        booster.append(_fetch_with_meta(entry["query"], entry.get("treatment")))
    else:
        wc = pick_weighted(cfg["wildcard_weights"])
        card = None
        for hook in hooks:
            res = hook("wildcard", cfg)
            card = res or card
        booster.append(card or fetch_random_card(sc, wc))

    # --- foil slot (table-aware, uses foil prices) ---
    foil = None
    if cfg.get("foil_table"):
        entry = pick_from_table(cfg["foil_table"])
        foil = _fetch_with_meta(entry["query"], entry.get("treatment"), force_foil=True)
    else:
        # legacy: MH3 fetchland lotto
        if cfg.get("foil_fetchlands"):
            if random.random() < cfg.get("foil_fetch_chance", 0.057):
                for _ in range(8):
                    cand = fetch_random_card(sc, "rare", is_foil=True)
                    if cand and cand.get("name") in cfg.get("fetchland_names", FETCHLAND_NAMES):
                        foil = cand; break
        if not foil:
            foil_rarity = pick_weighted(cfg["foil_weights"])
            foil = fetch_random_card(sc, foil_rarity, is_foil=True)

    # --- post-build hooks (OTP, CLB adds, etc.) ---
    for hook in hooks:
        extra = hook("post", cfg)
        if extra:
            if isinstance(extra, list):
                booster.extend([c for c in extra if c])
            elif isinstance(extra, dict):
                booster.append(extra)

    token_count = cfg.get("token_count", 1)
    return booster, foil, bonus_card, token_count

# =========================
# Tiny CLI
# =========================

def main():
    modes = {"1": "single", "2": "compare"}
    print("1. Open a single booster\n2. Compare two sets")
    m = input("Enter 1 or 2: ").strip()
    suspense = input("Reveal one by one? (y/n): ").strip().lower() == "y"

    valid = set(k for k in REGISTRY.keys() if not k.startswith("_")) | {
        "blb","mkm","lci","mom","one","bro","dmu","snc","neo","vow","mid","afr","stx","khm","znr","thb","cmm"
    }

    if modes.get(m) == "compare":
        def ask(prompt, exclude=None):
            while True:
                s = input(prompt).strip().lower()
                if s in valid and s != exclude:
                    return s
                print("Invalid set.")

        a = ask("First set: ")
        b = ask("Second set: ", exclude=a)
        totals = {a: 0.0, b: 0.0}

        for i in range(3):
            for s in (a, b):
                print(f"\n--- {s.upper()} Booster #{i+1} ---")
                booster, foil, bonus, token = open_booster(s)
                display_booster(booster, foil, bonus, token, suspense)

                def value(c, foil=False):
                    if not c: return 0.0
                    prices = c.get("prices", {})
                    k = "eur_foil" if foil else "eur"
                    v = prices.get(k) or prices.get("usd_foil" if foil else "usd")
                    try: return float(v) if v else 0.0
                    except: return 0.0

                tot = sum(value(c) for c in booster) + value(foil, True) + value(bonus)
                totals[s] += tot
                input("Press Enter...")

        print("\n=== Results ===")
        print(f"{a.upper()}: {totals[a]:.2f}€")
        print(f"{b.upper()}: {totals[b]:.2f}€")
        print("Winner:", (a if totals[a] > totals[b] else b if totals[b] > totals[a] else "Tie!").upper())
    else:
        s = input("\nSet code (e.g., eoe, mh3, woe): ").strip().lower()
        if s not in valid:
            print("Invalid set. Exiting.")
            return
        booster, foil, bonus, token = open_booster(s)
        display_booster(booster, foil, bonus, token, suspense)

if __name__ == "__main__":
    main()
