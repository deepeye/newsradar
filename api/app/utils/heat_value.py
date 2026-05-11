"""Parse Chinese heat_value strings to numeric scores."""


def parse_heat_value(value: str | None) -> float:
    """Convert heat_value (String field) to a float for scoring.

    Handles: "1234万" → 12340000, "5亿" → 500000000,
    "爆"/"热度爆表" → infinity, "1000000" → 1000000, None → 0.0
    """
    if value is None:
        return 0.0

    value = value.strip()

    if not value:
        return 0.0

    # Non-numeric keywords indicating extreme heat
    explosive_keywords = ("爆", "热度爆表", "爆表", "极热")
    if value in explosive_keywords:
        return float("inf")

    # Chinese suffix multipliers
    multipliers = {"万": 1e4, "亿": 1e8}

    suffix = None
    for s in multipliers:
        if value.endswith(s):
            suffix = s
            break

    if suffix:
        numeric_part = value[:-len(suffix)]
        try:
            return float(numeric_part) * multipliers[suffix]
        except ValueError:
            return 0.0

    # Pure numeric string
    try:
        return float(value)
    except ValueError:
        # Fallback: return 0 for unparseable strings
        return 0.0