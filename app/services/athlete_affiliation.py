"""Affiliation values are snapshots, independent of dictionary objects."""
from app.core.errors import APIError, ErrorCode
from app.models.location.location_object import LocationObject
from app.models.location.location_alias import LocationAlias
from app.shared.utils.location_text import normalize_location_text


async def athlete_text_fields(data):
    data = dict(data)
    alias = data.pop("alias", None)
    location_id = data.pop("location_object_id", None)
    location = None
    if location_id is not None:
        location = await LocationObject.get_or_none(id=location_id)
        if location is None:
            raise APIError(ErrorCode.LOCATION_OBJECT_NOT_FOUND)
    elif alias:
        rules = await LocationAlias.filter(alias_key=normalize_location_text(alias)).prefetch_related("location_object")
        candidates = []
        for rule in rules:
            value = rule.location_object
            if any(not data.get(k) for k in rule.required or []):
                continue
            if any(data.get(k) and getattr(value, k) and normalize_location_text(data[k]) != normalize_location_text(getattr(value, k)) for k in ("city", "region")):
                continue
            candidates.append(value)
        identities = {(v.club, v.city, v.region): v for v in candidates}
        if len(identities) == 1:
            location = next(iter(identities.values()))
    if location:
        for key in ("club", "city", "region"):
            if key not in data or data[key] is None:
                data[key] = getattr(location, key)
    elif alias and not data.get("club"):
        data["club"] = alias
    data["location_object_id"] = None
    return data
