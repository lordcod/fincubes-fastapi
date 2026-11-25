from difflib import SequenceMatcher

from tortoise.transactions import in_transaction

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.models.competition.competition import Competition
from app.models.competition.protocol_import import ProtocolImport
from app.models.competition.result import Result
from app.models.location.location_alias import LocationAlias
from app.models.location.location_object import LocationObject
from app.schemas.admin.protocol_import import PrepareImport
from app.services.location_catalog import (
    add_aliases_to_location_object,
    create_location_object,
    matches_required_location_context,
)
from app.shared.utils.flexible_time import FlexibleTime
from app.shared.utils.location_text import normalize_location_text


def normalized(value):
    return normalize_location_text(value or "").replace("ё", "е")


def location_data(location):
    return {"location_id": str(location.id), "club": location.club,
            "city": location.city, "region": location.region}


async def prepare_locations(payload):
    locations = await LocationObject.all()
    aliases = await LocationAlias.all()
    by_id = {str(location.id): location for location in locations}
    aliases_by_id = {}
    for alias in aliases:
        aliases_by_id.setdefault(str(alias.location_object_id), []).append(alias)
    matched, choices = {}, []
    for team in payload.teams:
        exact = set()
        ranked = []
        for location_id, location in by_id.items():
            rules = aliases_by_id.get(location_id, [])
            for rule in rules:
                if rule.alias_key == normalize_location_text(team.alias) and matches_required_location_context(
                    location, city=team.city, region=team.region, required=rule.required,
                ):
                    # Explicit source context must not contradict the location.
                    if all(not incoming or not stored or normalized(incoming) == normalized(stored)
                           for incoming, stored in ((team.city, location.city), (team.region, location.region))):
                        exact.add(location_id)
            names = [location.club or "", *[rule.alias for rule in rules]]
            score = max(SequenceMatcher(None, normalized(team.alias), normalized(name)).ratio() for name in names)
            if location_id in exact or score >= 0.35:
                ranked.append({**location_data(location), "similarity": round(score, 3),
                               "exact_alias": location_id in exact})
        ranked.sort(key=lambda row: (not row["exact_alias"], -row["similarity"], row["location_id"]))
        if len(exact) == 1:
            matched[team.key] = next(iter(exact))
        else:
            # All exact matches are retained, even if there are more than ten.
            candidates = [row for row in ranked if row["exact_alias"]]
            candidates += [row for row in ranked if not row["exact_alias"]][:10]
            choices.append({"key": team.key, "source": team.model_dump(), "candidates": candidates})
    return {"type": "locations", "import_id": str(payload.import_id),
            "matched": matched, "choices": choices}


async def prepare_athletes(payload, location_ids):
    # One bounded database fetch for the birth years present in this protocol.
    candidates = await Athlete.filter(birth_year__in=[str(a.birth_year) for a in payload.athletes]).prefetch_related("location_object")
    by_year = {}
    for candidate in candidates:
        by_year.setdefault(str(candidate.birth_year), []).append(candidate)
    matched, choices = {}, []
    for source in payload.athletes:
        rows, exact = [], []
        for candidate in by_year.get(str(source.birth_year), []):
            if candidate.gender.upper() != source.gender:
                continue
            same_name = (normalized(source.last_name) == normalized(candidate.last_name)
                         and normalized(source.first_name) == normalized(candidate.first_name))
            similarity = SequenceMatcher(None, normalized(f"{source.last_name} {source.first_name}"),
                                         normalized(f"{candidate.last_name} {candidate.first_name}")).ratio()
            if not same_name and similarity < 0.65:
                continue
            same_location = str(candidate.location_object_id) == location_ids[source.team_key]
            license_conflict = bool(source.license and candidate.license and source.license != candidate.license)
            if same_name and same_location and not license_conflict:
                exact.append(candidate.id)
            rows.append({"athlete_id": candidate.id, "last_name": candidate.last_name,
                         "first_name": candidate.first_name, "birth_year": candidate.birth_year,
                         "gender": candidate.gender, "license": candidate.license,
                         "location": location_data(candidate.location_object) if candidate.location_object_id else None,
                         "same_name": same_name, "same_location": same_location,
                         "license_conflict": license_conflict, "similarity": round(similarity, 3)})
        rows.sort(key=lambda row: (not row["same_name"], not row["same_location"], -row["similarity"], row["athlete_id"]))
        if len(exact) == 1:
            matched[source.key] = exact[0]
        else:
            choices.append({"key": source.key, "source": source.model_dump(mode="json", exclude={"results"}),
                            "candidates": [row for row in rows if row["same_name"]]
                            + [row for row in rows if not row["same_name"]][:10]})
    return {"type": "finish", "import_id": str(payload.import_id), "matched": matched, "choices": choices}


def check_decisions(decisions, keys, matched):
    if set(decisions) - keys or keys - (set(decisions) | set(matched)):
        raise APIError(ErrorCode.PROTOCOL_IMPORT_DECISIONS_REQUIRED)


async def process_protocol_import(request):
    async with in_transaction() as connection:
        if request.type == "prepare":
            competition = await Competition.filter(id=request.competition_id).using_db(connection).select_for_update().first()
            if competition is None:
                raise APIError(ErrorCode.COMPETITION_NOT_FOUND)
            draft = await ProtocolImport.filter(id=request.import_id).using_db(connection).first()
            payload = request.model_dump(mode="json")
            if draft:
                if draft.payload != payload:
                    raise APIError(ErrorCode.PROTOCOL_IMPORT_CONFLICT)
                return draft.state["response"]
            response = await prepare_locations(request)
            await ProtocolImport.create(id=request.import_id, competition_id=request.competition_id,
                                        payload=payload, state={"response": response}, using_db=connection)
            return response

        draft = await ProtocolImport.filter(id=request.import_id).using_db(connection).select_for_update().first()
        if draft is None:
            raise APIError(ErrorCode.PROTOCOL_IMPORT_NOT_FOUND)
        # Successful retries return the persisted response; changed decisions are rejected.
        if request.type == "finish" and draft.stage == "finish":
            if draft.state["finish_request"] != request.model_dump(mode="json"):
                raise APIError(ErrorCode.PROTOCOL_IMPORT_CONFLICT)
            return draft.state["response"]
        if request.type == "locations" and draft.stage in {"locations", "finish"}:
            if draft.state["locations_request"] != request.model_dump(mode="json"):
                raise APIError(ErrorCode.PROTOCOL_IMPORT_CONFLICT)
            return draft.state["athlete_response"]
        payload = PrepareImport.model_validate(draft.payload)
        if request.type == "locations":
            if draft.stage != "prepare":
                raise APIError(ErrorCode.PROTOCOL_IMPORT_CONFLICT)
            location_ids = dict(draft.state["response"]["matched"])
            check_decisions(request.decisions, {team.key for team in payload.teams}, location_ids)
            for team in payload.teams:
                decision = request.decisions.get(team.key)
                if decision is None:
                    continue
                if decision.action == "existing":
                    location = await LocationObject.get_or_none(id=decision.location_id)
                    if location is None:
                        raise APIError(ErrorCode.LOCATION_OBJECT_NOT_FOUND)
                    await add_aliases_to_location_object(location.id, [team.alias], decision.required)
                else:
                    data = decision.location.model_dump()
                    data["aliases"] = list(dict.fromkeys([*data["aliases"], team.alias]))
                    location = await create_location_object(type(decision.location).model_validate(data))
                location_ids[team.key] = str(location.id)
            # Aliases and locations are committed at this stage, not in finish.
            response = await prepare_athletes(payload, location_ids)
            draft.stage = "locations"
            draft.state = {"locations": location_ids, "locations_request": request.model_dump(mode="json"),
                           "athlete_response": response, "response": response}
        else:
            if draft.stage != "locations":
                raise APIError(ErrorCode.PROTOCOL_IMPORT_CONFLICT)
            # Serialize imports into this competition, including athlete creation.
            await Competition.filter(id=draft.competition_id).using_db(connection).select_for_update().first()
            athlete_ids = dict(draft.state["athlete_response"]["matched"])
            check_decisions(request.decisions, {a.key for a in payload.athletes}, athlete_ids)
            created = []
            for source in payload.athletes:
                decision = request.decisions.get(source.key)
                if decision and decision.action == "existing":
                    athlete_ids[source.key] = decision.athlete_id
                elif decision and decision.action == "create":
                    athlete = await Athlete.create(
                        last_name=source.last_name, first_name=source.first_name,
                        birth_year=str(source.birth_year), gender=source.gender, license=source.license,
                        location_object_id=draft.state["locations"][source.team_key], using_db=connection,
                    )
                    athlete_ids[source.key] = athlete.id
                    created.append(athlete.id)
            existing = await Athlete.filter(id__in=list(athlete_ids.values())).using_db(connection).select_for_update()
            if {a.id for a in existing} != set(athlete_ids.values()):
                raise APIError(ErrorCode.ATHLETE_NOT_FOUND)
            # Revalidate automatically selected identities if profiles changed between calls.
            by_id = {a.id: a for a in existing}
            for source in payload.athletes:
                if source.key in request.decisions:
                    continue
                athlete = by_id[athlete_ids[source.key]]
                if (normalized(athlete.last_name) != normalized(source.last_name)
                        or normalized(athlete.first_name) != normalized(source.first_name)
                        or str(athlete.birth_year) != str(source.birth_year)
                        or athlete.gender.upper() != source.gender
                        or str(athlete.location_object_id) != draft.state["locations"][source.team_key]
                        or (source.license and athlete.license and source.license != athlete.license)):
                    raise APIError(ErrorCode.PROTOCOL_IMPORT_CONFLICT)
            results = []
            for source in payload.athletes:
                for item in source.results:
                    data = item.model_dump()
                    for field in ("result", "final"):
                        data[field] = FlexibleTime.validate(data[field]) if data[field] is not None else None
                    data["metadata"] = {**data["metadata"], "protocol_import": {
                        "id": str(draft.id), "athlete_key": source.key,
                        "team": next(t.model_dump() for t in payload.teams if t.key == source.team_key),
                        "location_id": draft.state["locations"][source.team_key],
                    }}
                    results.append(Result(athlete_id=athlete_ids[source.key], competition_id=draft.competition_id, **data))
            await Result.bulk_create(results, using_db=connection)
            response = {"type": "finished", "import_id": str(draft.id), "athletes": athlete_ids,
                        "created_athlete_ids": created, "results_created": len(results)}
            draft.stage = "finish"
            draft.state = {**draft.state, "finish_request": request.model_dump(mode="json"), "response": response}
        await draft.save(using_db=connection, update_fields=["stage", "state", "updated_at"])
        return response
