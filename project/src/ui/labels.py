"""Display-name helpers. Model keys stay snake_case; the UI reads Title Case."""
from __future__ import annotations

#: Tokens that must keep their own casing rather than be title-cased.
ACRONYMS = {
    "dri": "DRI", "abc": "ABC", "whr": "WHR", "sec": "SEC", "co": "CO",
    "co2": "CO2", "h2": "H2", "h2o": "H2O", "o2": "O2", "n2": "N2",
    "so2": "SO2", "cao": "CaO", "mgo": "MgO", "fe": "Fe", "feo": "FeO",
    "fe2o3": "Fe2O3", "c": "C", "s": "S", "h": "H", "o": "O",
    "capex": "CAPEX", "opex": "OPEX", "inr": "INR", "mw": "MW",
    "kwh": "kWh", "mwh": "MWh", "tpd": "TPD", "gcal": "Gcal", "kj": "kJ",
    "ipcc": "IPCC", "ceew": "CEEW", "teri": "TERI", "bee": "BEE",
    "v.m.": "V.M.", "esp": "ESP", "afbc": "AFBC",
}
#: Small words that stay lower-case unless they open the string.
MINOR = {"a", "an", "and", "as", "at", "by", "for", "in", "of", "on", "or",
         "the", "to", "vs", "with", "per"}


def _split_hyphen(word: str) -> list[str]:
    if "-" not in word or word.startswith("-"):
        return [word]
    parts = word.split("-")
    return [p + "-" if i < len(parts) - 1 else p for i, p in enumerate(parts)]


def title_case(text: str) -> str:
    """Title-case a model label while protecting acronyms and formulae."""
    words = text.replace("_", " ").split()
    # Hyphenated compounds title-case each part: waste-gas -> Waste-Gas.
    words = [w for word in words for w in _split_hyphen(word)]
    out = []
    for i, w in enumerate(words):
        core = w.strip("()[],.:").lower()
        lead = w[:len(w) - len(w.lstrip("(["))]
        trail = w[len(w.rstrip(")],.:")):]
        stripped = w.strip("()[],.:")
        if any(ch.isupper() for ch in stripped[1:]):
            body = stripped              # already mixed-case: CaO+MgO, Fe2O3
        elif core in ACRONYMS:
            body = ACRONYMS[core]
        elif core in MINOR and i != 0:
            body = core
        elif any(ch.isdigit() for ch in core) and any(ch.isalpha() for ch in core):
            body = w.strip("()[],.:")          # leave formulae like 2FeO alone
        else:
            body = core[:1].upper() + core[1:]
        out.append(f"{lead}{body}{trail}")
    joined = ""
    for w in out:
        joined += w if (not joined or joined.endswith("-")) else " " + w
    return joined


#: Stream names read better when rewritten rather than mechanically cased.
STREAM_NAMES = {
    "iron ore (dry)": "Iron Ore",
    "ore moisture": "Ore Moisture",
    "feed coal": "Feed Coal",
    "injection coal": "Injection Coal",
    "dolomite": "Dolomite",
    "combustion air": "Combustion Air",
    "DRI": "Sponge Iron (DRI)",
    "char (dolochar)": "Dolochar",
    "flue dust": "Flue Dust",
    "calcined flux (CaO+MgO)": "Calcined Flux",
    "free ash to cooler": "Free Ash",
    "other unreduced fines": "Unreduced Fines",
    "waste gas": "Waste Gas",
}

ENERGY_GROUPS = {
    "chemical energy out (unburnt)": "Chemical Energy",
    "endothermic process demand": "Process Demand",
    "sensible heat out": "Sensible Heat",
    "losses": "Losses",
}

COST_LINES = {
    "iron ore": "Iron Ore",
    "coal": "Coal",
    "dolomite": "Dolomite",
    "purchased power": "Purchased Power",
    "other retrofit OPEX": "Retrofit OPEX",
    "fixed OPEX": "Fixed OPEX",
    "dolochar credit": "Dolochar Credit",
    "power export revenue": "Power Export Revenue",
    "annualised CAPEX": "Annualised CAPEX",
}


def stream(name: str) -> str:
    return STREAM_NAMES.get(name, title_case(name))
