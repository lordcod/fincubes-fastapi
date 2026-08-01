import re
import unicodedata


def normalize_location_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().casefold()
    normalized = normalized.replace("ё", "е")
    normalized = normalized.replace("С‘", "Рµ")
    return re.sub(r"\s+", " ", normalized)
