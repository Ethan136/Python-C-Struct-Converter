"""Central type registry for size/alignment and aliases.

This module introduces a unified API for resolving C/C++ types used by the
parser and layout calculators. It separates:

- BASE_TYPE_INFO: built-in, standard types (x86_64-like defaults)
- CUSTOM_TYPE_INFO: optional project/user overrides loaded from config
- ALIAS_MAP: type aliases mapped to canonical types (e.g., U32 -> unsigned int)

Downstream code should use ``normalize_type`` and ``get_type_info``.
"""

from __future__ import annotations

from typing import Dict, Optional
import os


# --- Built-in base types (previously TYPE_INFO) ------------------------------
BASE_TYPE_INFO: Dict[str, Dict[str, int]] = {
    "char":               {"size": 1, "align": 1},
    "signed char":        {"size": 1, "align": 1},
    "unsigned char":      {"size": 1, "align": 1},
    "bool":               {"size": 1, "align": 1},
    "short":              {"size": 2, "align": 2},
    "unsigned short":     {"size": 2, "align": 2},
    "int":                {"size": 4, "align": 4},
    "unsigned int":       {"size": 4, "align": 4},
    "long":               {"size": 8, "align": 8},
    "unsigned long":      {"size": 8, "align": 8},
    "long long":          {"size": 8, "align": 8},
    "unsigned long long": {"size": 8, "align": 8},
    "float":              {"size": 4, "align": 4},
    "double":             {"size": 8, "align": 8},
    "pointer":            {"size": 8, "align": 8},
}


# --- Defaults for aliases and custom types -----------------------------------

DEFAULT_ALIAS_MAP: Dict[str, str] = {
    # User-requested shorthand aliases
    "U8":  "unsigned char",
    "U16": "unsigned short",
    "U32": "unsigned int",
    "U64": "unsigned long long",
}

CUSTOM_TYPE_INFO: Dict[str, Dict[str, int]] = {}
ALIAS_MAP: Dict[str, str] = dict(DEFAULT_ALIAS_MAP)


def _load_yaml_if_available(path: str) -> Optional[dict]:
    if not os.path.exists(path):
        return None
    try:
        import yaml  # type: ignore
    except Exception:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return None


def _bootstrap_from_config() -> None:
    # Allow overriding config locations via env vars if desired
    base_dir = os.path.join(os.getcwd(), "config")
    alias_path = os.environ.get("TYPE_ALIASES_PATH", os.path.join(base_dir, "type_aliases.yaml"))
    custom_path = os.environ.get("CUSTOM_TYPES_PATH", os.path.join(base_dir, "custom_types.yaml"))

    data = _load_yaml_if_available(alias_path)
    if isinstance(data, dict):
        aliases = data.get("aliases", {})
        if isinstance(aliases, dict):
            for k, v in aliases.items():
                if isinstance(k, str) and isinstance(v, str):
                    ALIAS_MAP[k.strip()] = " ".join(v.split())

    data2 = _load_yaml_if_available(custom_path)
    if isinstance(data2, dict):
        types = data2.get("types", {})
        if isinstance(types, dict):
            for k, meta in types.items():
                if isinstance(meta, dict) and "size" in meta and "align" in meta:
                    try:
                        size = int(meta["size"])  # type: ignore
                        align = int(meta["align"])  # type: ignore
                        CUSTOM_TYPE_INFO[" ".join(k.split())] = {"size": size, "align": align}
                    except Exception:
                        pass


_bootstrap_from_config()


def normalize_type(type_name: str) -> str:
    """Normalize a type using alias map (idempotent)."""
    t = " ".join((type_name or "").split())
    return ALIAS_MAP.get(t, t)


def get_type_info(type_name: str) -> Dict[str, int]:
    """Return a dict with keys {size, align} for the given type.

    Resolution order: alias normalization -> CUSTOM_TYPE_INFO -> BASE_TYPE_INFO.
    Raises KeyError if not found.
    """
    canonical = normalize_type(type_name)
    if canonical in CUSTOM_TYPE_INFO:
        return CUSTOM_TYPE_INFO[canonical]
    if canonical in BASE_TYPE_INFO:
        return BASE_TYPE_INFO[canonical]
    raise KeyError(f"Unknown type: {type_name}")


# Backward compatibility: a merged TYPE_INFO view where custom overrides base.
def merged_type_info() -> Dict[str, Dict[str, int]]:
    merged = dict(BASE_TYPE_INFO)
    merged.update(CUSTOM_TYPE_INFO)
    return merged


