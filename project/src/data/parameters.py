"""Parameter store with provenance.

Every number the model uses is loaded from config/parameters.json, where it
carries its source, a plausible min/max range and a provenance status. Nothing
numeric should be hardcoded in a model module -- if you find yourself typing a
magic number, add it to the JSON instead.
"""
from __future__ import annotations

import json
import os

_CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "config")

#: Thermodynamic and stoichiometric constants. These are genuine physical
#: constants, not assumptions, so they live in code rather than in the config.
MW = {
    "Fe": 55.845, "O": 15.999, "O2": 31.998, "C": 12.011, "H2": 2.016,
    "Fe2O3": 159.687, "FeO": 71.844, "CO": 28.010, "CO2": 44.009,
    "H2O": 18.015, "N2": 28.014, "CaO": 56.077, "MgO": 40.304,
    "CaCO3": 100.086, "dolomite": 184.401,
}

#: Standard enthalpies of reaction at 298 K, kJ per mol of the first reactant.
#: Sign convention: positive = endothermic (heat absorbed by the process).
DH_KJ_PER_MOL = {
    "Fe2O3+CO->2FeO+CO2": -2.8,
    "FeO+CO->Fe+CO2": -11.0,
    "C+CO2->2CO": 172.5,
    "CO+0.5O2->CO2": -283.0,
    "C+O2->CO2": -393.5,
    "H2+0.5O2->H2O": -241.8,
    "Fe2O3+3H2->2Fe+3H2O": 98.8,
    "dolomite->CaO+MgO+2CO2": 301.0,
}

GCAL_PER_KJ = 1.0 / 4.1868e6
KJ_PER_KWH = 3600.0
LATENT_HEAT_WATER_KJ_KG = 2257.0


class Parameters:
    """Dict-like access to the parameter set, with provenance preserved.

    >>> p = Parameters()
    >>> p["ore.fe_total_frac"]
    0.63
    >>> p.meta("ore.fe_total_frac")["status"]
    'verified'
    """

    def __init__(self, path: str | None = None, overrides: dict | None = None):
        self.path = path or os.path.join(_CONFIG_DIR, "parameters.json")
        with open(self.path) as fh:
            raw = json.load(fh)
        self._meta_block = raw.get("_meta", {})
        self._entries = {k: v for k, v in raw.items() if not k.startswith("_")}
        self._overrides: dict = {}
        if overrides:
            self.override(overrides)

    # -- access ----------------------------------------------------------
    def __getitem__(self, key: str):
        if key in self._overrides:
            return self._overrides[key]
        try:
            return self._entries[key]["value"]
        except KeyError:
            raise KeyError(
                f"Unknown parameter {key!r}. Add it to {os.path.basename(self.path)} "
                f"rather than hardcoding it."
            ) from None

    def __contains__(self, key: str) -> bool:
        return key in self._entries

    def get(self, key: str, default=None):
        return self[key] if key in self._entries or key in self._overrides else default

    def meta(self, key: str) -> dict:
        return dict(self._entries[key])

    def bounds(self, key: str):
        """Return the (min, max) plausible range, falling back to +/-20%.

        Non-numeric parameters (mode switches such as coal.rate_mode) have no
        range, so both bounds come back as None rather than raising.
        """
        e = self._entries[key]
        v = e["value"]
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            return (e.get("min"), e.get("max"))
        return (e.get("min", v * 0.8), e.get("max", v * 1.2))

    # -- mutation --------------------------------------------------------
    def override(self, values: dict) -> "Parameters":
        """Override values in place (used by the UI and by sensitivity sweeps)."""
        for k, v in values.items():
            if k not in self._entries:
                raise KeyError(f"Cannot override unknown parameter {k!r}.")
            self._overrides[k] = v
        return self

    def with_overrides(self, values: dict) -> "Parameters":
        """Return an independent copy carrying `values` on top of this set."""
        clone = Parameters(self.path)
        clone._overrides = dict(self._overrides)
        clone.override(values)
        return clone

    def clear_overrides(self) -> None:
        self._overrides.clear()

    # -- provenance ------------------------------------------------------
    @property
    def calibration_plant(self) -> str:
        return self._meta_block.get("calibration_plant", "")

    def keys(self):
        return self._entries.keys()

    def numeric_keys(self) -> list[str]:
        """Parameters that carry a numeric value, i.e. are sweepable."""
        return [k for k, e in self._entries.items()
                if isinstance(e["value"], (int, float))
                and not isinstance(e["value"], bool)]

    def sensitivity_keys(self) -> list[str]:
        """Parameters flagged as needing a sensitivity study."""
        numeric = set(self.numeric_keys())
        return [k for k, e in self._entries.items()
                if e.get("sensitivity") and k in numeric]

    def out_of_range(self) -> list[dict]:
        """Numeric values, overrides included, that fall outside their min/max.

        The bounds are the plausible range from the literature, so a value
        outside them is not necessarily wrong, but it is no longer supported
        by the sources and the caller should say so.
        """
        rows = []
        for k in self.numeric_keys():
            v = self[k]
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                continue
            lo, hi = self.bounds(k)
            if (lo is not None and v < lo) or (hi is not None and v > hi):
                rows.append({"parameter": k, "value": v, "min": lo, "max": hi,
                             "overridden": k in self._overrides})
        return rows

    def unsourced_keys(self) -> list[str]:
        """Parameters not yet traced to a source in data/text/."""
        return [k for k, e in self._entries.items()
                if e.get("status") == "needs_citation"]

    def provenance_rows(self) -> list[dict]:
        """Flat table of every parameter and its provenance, for display/export."""
        rows = []
        for k, e in self._entries.items():
            lo, hi = self.bounds(k)
            rows.append({
                "parameter": k,
                "value": self[k],
                "config_value": e["value"],
                "overridden": k in self._overrides,
                "unit": e.get("unit", ""),
                "min": lo,
                "max": hi,
                "status": e.get("status", ""),
                "sensitivity_required": bool(e.get("sensitivity")),
                "source": e.get("source", ""),
                "source_file": e.get("source_file", ""),
                "notes": e.get("notes", ""),
            })
        return rows

    def provenance_summary(self) -> dict:
        counts: dict = {}
        for e in self._entries.values():
            s = e.get("status", "unknown")
            counts[s] = counts.get(s, 0) + 1
        counts["total"] = len(self._entries)
        return counts


def load_validation_targets(path: str | None = None) -> list[dict]:
    """Literature acceptance bands for model outputs."""
    path = path or os.path.join(_CONFIG_DIR, "validation_targets.json")
    with open(path) as fh:
        return json.load(fh)["targets"]


if __name__ == "__main__":
    p = Parameters()
    print("Provenance:", p.provenance_summary())
    print("Needs citation:", len(p.unsourced_keys()))
    print("Sensitivity-flagged:", len(p.sensitivity_keys()))
    print("Calibration plant:", p.calibration_plant)
