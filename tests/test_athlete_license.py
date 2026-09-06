from app.services.athlete_license import (
    highest_automatic_license,
    normalize_license,
)


def test_highest_automatic_license_is_capped_at_kms():
    assert highest_automatic_license(["IIIЮН", "КМС", "МС", "МСМК"]) == "КМС"


def test_highest_automatic_license_ignores_unknown_values():
    assert highest_automatic_license(["II", "неизвестный"]) == "II"


def test_license_normalization_supports_common_aliases():
    assert normalize_license(" msmk ") == "МСМК"
    assert normalize_license("cms") == "КМС"
    assert normalize_license("III ЮН") == "IIIЮН"
