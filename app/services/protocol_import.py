"""Two-phase protocol import. All domain writes happen in finish's transaction."""
from datetime import datetime, timezone
from difflib import SequenceMatcher
import hashlib
import json

from tortoise.transactions import in_transaction

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.models.competition.competition import Competition
from app.models.competition.distance import Distance
from app.models.competition.protocol_import import ProtocolImport
from app.models.competition.result import Result
from app.models.competition.relay_result import RelayResult
from app.models.competition.relay_leg import RelayLeg
from app.models.location.location_alias import LocationAlias
from app.schemas.admin.protocol_import import PrepareImport, OmitRecord
from app.services.athlete_license import normalize_license, highest_automatic_license, MANUAL_LICENSES
from app.shared.utils.flexible_time import FlexibleTime
from app.shared.utils.location_text import normalize_location_text


def normalized(value):
    return normalize_location_text(value or "").replace("ё", "е")


def affiliation(value):
    return {k: getattr(value, k, None) or None for k in ("club", "city", "region")}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def event_identity(event):
    fields = ("stroke", "distance", "relay_count", "gender", "category", "min_year", "max_year")
    return {k: getattr(event, k) for k in fields}


async def prepare_teams(payload):
    rules = await LocationAlias.all().prefetch_related("location_object")
    output = {}
    for team in payload.teams:
        candidates = {}
        for rule in rules:
            location = rule.location_object
            if normalized(rule.alias) != normalized(team.alias):
                continue
            if any(getattr(team, k) and getattr(location, k) and
                   normalized(getattr(team, k)) != normalized(getattr(location, k)) for k in ("city", "region")):
                continue
            if any(not getattr(team, k) for k in rule.required or []):
                continue
            fields = affiliation(location)
            candidates[digest(fields)] = fields
        rows = list(candidates.values())
        output[team.key] = {"source": team.model_dump(), "candidates": rows,
                            "fields": rows[0] if len(rows) == 1 else
                            {"club": team.alias, "city": team.city, "region": team.region}}
    return output


async def prepare_athletes(payload, teams):
    candidates = await Athlete.filter(birth_year__in=list({str(a.birth_year) for a in payload.athletes}))
    matched, choices = {}, []
    for source in payload.athletes:
        rows = []
        for candidate in candidates:
            if str(source.birth_year) != candidate.birth_year or source.gender != candidate.gender.upper():
                continue
            same = normalized(source.last_name) == normalized(candidate.last_name) and normalized(source.first_name) == normalized(candidate.first_name)
            score = SequenceMatcher(None, normalized(source.last_name + " " + source.first_name),
                                    normalized(candidate.last_name + " " + candidate.first_name)).ratio()
            if not same and score < 0.65:
                continue
            team = teams.get(source.team_key, {}).get("fields", {})
            compatible = all(not team.get(k) or not getattr(candidate, k) or
                             normalized(team[k]) == normalized(getattr(candidate, k)) for k in ("club", "city", "region"))
            rows.append({"athlete_id": candidate.id, "last_name": candidate.last_name,
                         "first_name": candidate.first_name, "birth_year": candidate.birth_year,
                         "gender": candidate.gender, "license": candidate.license, **affiliation(candidate),
                         "same_name": same, "compatible_team": compatible, "similarity": round(score, 3)})
        exact = [r for r in rows if r["same_name"]]
        # Changed club or rank is not a new person; namesakes still require a decision.
        if len(exact) == 1:
            matched[source.key] = exact[0]["athlete_id"]
        rows.sort(key=lambda r: (not r["same_name"], not r["compatible_team"], -r["similarity"]))
        choices.append({"key": source.key, "source": source.model_dump(exclude={"results"}),
                        "matched": exact[0] if len(exact) == 1 else None,
                        "candidates": [r for r in rows if r["same_name"]] + [r for r in rows if not r["same_name"]][:10]})
    # Do not silently merge two source identities into the same profile.
    repeated = {v for v in matched.values() if list(matched.values()).count(v) > 1}
    matched = {k: v for k, v in matched.items() if v not in repeated}
    for row in choices:
        if row["key"] not in matched:
            row["matched"] = None
    return {"matched": matched, "athletes": choices}


async def competition_choices(payload):
    if payload.competition_id is not None:
        rows = await Competition.filter(id=payload.competition_id)
        if not rows:
            raise APIError(ErrorCode.COMPETITION_NOT_FOUND)
    else:
        c = payload.competition
        rows = await Competition.filter(start_date=c.start_date, end_date=c.end_date)
        rows = [r for r in rows if normalized(r.name) == normalized(c.name)
                and (not c.city or not r.city or normalized(c.city) == normalized(r.city))
                and (not c.course or not r.course or c.course == r.course)]
    return [{"id": c.id, "name": c.name, "start_date": str(c.start_date), "end_date": str(c.end_date),
             "city": c.city, "course": c.course} for c in rows]


async def replacement_plan(competition_id):
    results = await Result.filter(competition_id=competition_id).order_by("id")
    relays = await RelayResult.filter(competition_id=competition_id).order_by("id")
    legs = await RelayLeg.filter(relay_result_id__in=[r.id for r in relays]).order_by("id")
    version = [(type(r).__name__, r.id, str(r.updated_at)) for r in [*results, *relays, *legs]]
    return {"result_ids": [r.id for r in results], "relay_ids": [r.id for r in relays],
            "token": digest([competition_id, version])}


async def existing_records(competition_id):
    if competition_id is None:
        return {"results": [], "relays": []}
    results = await Result.filter(competition_id=competition_id).values(
        "id", "athlete_id", "stroke", "distance", "result", "final", "place", "final_rank", "status", "metadata")
    relays = await RelayResult.filter(competition_id=competition_id).values(
        "id", "name", "stroke", "distance", "relay_count", "gender", "result", "place", "status", "metadata")
    return json.loads(json.dumps({"results": results, "relays": relays}, default=str))


async def get_protocol_import(import_id):
    draft = await ProtocolImport.get_or_none(id=import_id)
    if draft is None:
        raise APIError(ErrorCode.PROTOCOL_IMPORT_NOT_FOUND)
    return {"import_id": str(draft.id), "stage": draft.stage, "response": draft.state["response"]}


def official_data(item, event, source, import_id, team=None):
    data = item.model_dump(exclude={"key", "event_key", "round", "dsq_reason", "legs"})
    for field in ("result", "final"):
        if field in data and data[field] is not None:
            data[field] = FlexibleTime.validate(data[field])
    data["metadata"] = {**data.get("metadata", {}), "protocol_import": {
        "id": str(import_id), "key": item.key, "event": event_identity(event),
        "round": item.round, "source": source, "team": team,
        "dsq_reason": getattr(item, "dsq_reason", None)}}
    return data


def same_value(a, b):
    return str(a) == str(b) if a is not None and b is not None else a is b


async def write_result(model, data, identity, event, round_name, mode, connection, selected_id=None):
    rows = await model.filter(**identity).using_db(connection)
    if selected_id is not None:
        rows = [row for row in rows if row.id == selected_id]
        if len(rows) != 1:
            raise APIError(ErrorCode.PROTOCOL_IMPORT_CONFLICT)
    matching, legacy = [], []
    for row in rows:
        provenance = (row.metadata or {}).get("protocol_import", {})
        if selected_id is not None:
            matching.append(row)
        elif "event" not in provenance:
            legacy.append(row)
        elif provenance["event"] == event_identity(event) and provenance.get("round") == round_name:
            matching.append(row)
    if legacy or len(matching) > 1:
        return None, "ambiguous_existing_result"
    if matching:
        row = matching[0]
        same_fields = all(same_value(getattr(row, k), v) for k, v in data.items() if k != "metadata")
        old_metadata = {k: v for k, v in (row.metadata or {}).items() if k != "protocol_import"}
        new_metadata = {k: v for k, v in data["metadata"].items() if k != "protocol_import"}
        same_reason = (row.metadata or {}).get("protocol_import", {}).get("dsq_reason") == data["metadata"]["protocol_import"].get("dsq_reason")
        if same_fields and (mode == "append" or (old_metadata == new_metadata and same_reason)):
            return row, "unchanged"
        if mode == "append":
            return None, "existing_result_differs"
        row.update_from_dict(data)
        await row.save(using_db=connection)
        return row, "updated"
    return await model.create(**identity, **data, using_db=connection), "created"


async def process_protocol_import(request):
    async with in_transaction() as connection:
        # Serializes importer writes, including new competitions and shared athletes.
        await connection.execute_query("SELECT pg_advisory_xact_lock(706726, 2)")
        draft = await ProtocolImport.filter(id=request.import_id).using_db(connection).select_for_update().first()
        if request.type == "prepare":
            payload_json = request.model_dump(mode="json")
            if draft:
                if draft.payload != payload_json:
                    raise APIError(ErrorCode.PROTOCOL_IMPORT_CONFLICT)
                return draft.state["response"]
            competitions = await competition_choices(request)
            teams = await prepare_teams(request)
            athletes = await prepare_athletes(request, teams)
            cid = competitions[0]["id"] if len(competitions) == 1 else None
            plan = await replacement_plan(cid) if cid and request.mode == "replace" else None
            response = {"type": "finish", "import_id": str(request.import_id), "version": 2,
                        "competition": {"matched_id": cid, "candidates": competitions, "will_create": not competitions},
                        "teams": teams, **athletes, "replacement": plan,
                        "existing_records": {str(c["id"]): await existing_records(c["id"]) for c in competitions}}
            await ProtocolImport.create(id=request.import_id, competition_id=cid, payload=payload_json,
                                        state={"version": 2, "response": response, "prepared": response}, using_db=connection)
            return response
        if draft is None:
            raise APIError(ErrorCode.PROTOCOL_IMPORT_NOT_FOUND)
        if draft.state.get("version") != 2:
            raise APIError(ErrorCode.PROTOCOL_IMPORT_CONFLICT)
        request_json = request.model_dump(mode="json")
        if draft.stage == "finish":
            if draft.state["finish_request"] != request_json:
                raise APIError(ErrorCode.PROTOCOL_IMPORT_CONFLICT)
            return draft.state["response"]
        payload = PrepareImport.model_validate(draft.payload)
        prepared = draft.state["prepared"]
        # Keep omitted decisions until explicitly changed; no record disappears on resume.
        previous_request = draft.state.get("effective_request", draft.state.get("finish_request", {}))
        for field in ("results", "relays"):
            previous = previous_request.get(field, {})
            if previous:
                combined = {k: OmitRecord.model_validate(v) for k, v in previous.items()}
                # An explicit selected ID resumes a previously omitted result.
                selected = request.result_ids if field == "results" else request.relay_ids
                combined = {k: v for k, v in combined.items() if k not in selected and k not in request.resume}
                combined.update(getattr(request, field))
                setattr(request, field, combined)
        for key, value in previous_request.get("decisions", {}).items():
            if key not in request.decisions and key not in request.resume and value["action"] in {"skip", "defer"}:
                request.decisions[key] = OmitRecord.model_validate(value)
        athlete_keys = {a.key for a in payload.athletes}
        result_keys = {r.key for a in payload.athletes for r in a.results}
        if (set(request.decisions) - athlete_keys or set(request.teams) - {t.key for t in payload.teams}
                or (set(request.results) | set(request.result_ids)) - result_keys
                or (set(request.relays) | set(request.relay_ids)) - {r.key for r in payload.relays}
                or len(set(request.result_ids.values())) != len(request.result_ids)
                or len(set(request.relay_ids.values())) != len(request.relay_ids)
                or set(request.resume) - (athlete_keys | result_keys | {r.key for r in payload.relays})
                or set(request.results) & set(request.result_ids)
                or set(request.relays) & set(request.relay_ids)):
            raise APIError(ErrorCode.PROTOCOL_IMPORT_DECISIONS_REQUIRED)
        cid = request.competition_id or draft.competition_id
        candidates = await competition_choices(payload)
        allowed_ids = {r["id"] for r in candidates}
        if cid and draft.stage != "partial" and cid not in allowed_ids:
            raise APIError(ErrorCode.PROTOCOL_IMPORT_CONFLICT)
        if draft.stage == "partial" and cid != draft.competition_id:
            raise APIError(ErrorCode.PROTOCOL_IMPORT_CONFLICT)
        if cid is None:
            if len(candidates) > 1:
                return {**prepared, "competition": {"matched_id": None, "candidates": candidates, "will_create": False}}
            if candidates:
                cid = candidates[0]["id"]
            else:
                data = payload.competition.model_dump()
                competition = await Competition.create(**data, date=f"{data['start_date']} — {data['end_date']}", links=[], using_db=connection)
                cid = competition.id
        competition = await Competition.filter(id=cid).using_db(connection).select_for_update().first()
        if competition is None:
            raise APIError(ErrorCode.COMPETITION_NOT_FOUND)
        draft.competition_id = cid
        teams = {k: dict(v) for k, v in draft.state.get("teams", prepared["teams"]).items()}
        for key, value in request.teams.items():
            teams[key] = {**teams[key], "fields": value.model_dump()}
        if draft.stage == "partial" and teams != draft.state["teams"]:
            raise APIError(ErrorCode.PROTOCOL_IMPORT_CONFLICT)
        current = await prepare_athletes(payload, teams)
        saved_ids = draft.state.get("athletes", {})
        athlete_ids = {**current["matched"], **saved_ids}
        omitted, issues = [], []
        for key, athlete_id in prepared["matched"].items():
            if key not in request.decisions and key not in saved_ids and current["matched"].get(key) != athlete_id:
                athlete_ids.pop(key, None)
        for source in payload.athletes:
            decision = request.decisions.get(source.key)
            if source.key in saved_ids:
                previous = previous_request.get("decisions", {}).get(source.key)
                unchanged = decision and decision.model_dump() == previous
                if decision and not unchanged and (decision.action != "existing" or decision.athlete_id != saved_ids[source.key]):
                    raise APIError(ErrorCode.PROTOCOL_IMPORT_CONFLICT)
                continue
            if decision and decision.action in {"skip", "defer"}:
                athlete_ids.pop(source.key, None)
                omitted.append({"kind": "athlete", "key": source.key, **decision.model_dump()})
            elif decision and decision.action == "existing":
                athlete_ids[source.key] = decision.athlete_id
            elif decision and decision.action == "create":
                athlete_ids.pop(source.key, None)
            elif not decision and source.key not in athlete_ids:
                issues.append({"kind": "athlete", "key": source.key, "reason": "decision_required"})
        if len(set(athlete_ids.values())) != len(athlete_ids):
            raise APIError(ErrorCode.PROTOCOL_IMPORT_CONFLICT)
        existing = await Athlete.filter(id__in=list(athlete_ids.values())).using_db(connection).select_for_update()
        if {a.id for a in existing} != set(athlete_ids.values()):
            raise APIError(ErrorCode.ATHLETE_NOT_FOUND)
        if payload.mode == "replace" and draft.stage != "partial":
            plan = await replacement_plan(cid)
            if request.replace_token != plan["token"]:
                response = {**prepared, "replacement": plan, "competition": {"matched_id": cid, "candidates": candidates, "will_create": False}}
                draft.state = {**draft.state, "response": response}
                await draft.save(using_db=connection)
                return response
            # Replacement cannot partially delete a competition.
            if issues or omitted or request.results or request.relays or request.result_ids or request.relay_ids:
                raise APIError(ErrorCode.PROTOCOL_IMPORT_DECISIONS_REQUIRED)
            await Result.filter(competition_id=cid).using_db(connection).delete()
            await RelayResult.filter(competition_id=cid).using_db(connection).delete()
        counts = dict(draft.state.get("counts", {"athletes_created": 0, "licenses_updated": 0,
                         "results_created": 0, "results_updated": 0, "results_unchanged": 0,
                         "relays_created": 0, "relays_updated": 0, "relays_unchanged": 0, "distances_created": 0}))
        for source in payload.athletes:
            decision = request.decisions.get(source.key)
            if source.key not in saved_ids and decision and decision.action == "create":
                fields = teams.get(source.team_key, {}).get("fields", {})
                athlete = await Athlete.create(last_name=source.last_name, first_name=source.first_name,
                    birth_year=str(source.birth_year), gender=source.gender, license=source.license, **fields, using_db=connection)
                athlete_ids[source.key] = athlete.id
                counts["athletes_created"] += 1
        events = {e.key: e for e in payload.distances}
        for event in payload.distances:
            identity = event_identity(event)
            if not await Distance.filter(competition_id=cid, **identity).using_db(connection).exists():
                await Distance.create(competition_id=cid, order=event.order, **identity, using_db=connection)
                counts["distances_created"] += 1
        done_results = set(draft.state.get("done_results", []))
        done_relays = set(draft.state.get("done_relays", []))
        for source in payload.athletes:
            for item in source.results:
                if item.key in done_results:
                    if item.key in request.results:
                        raise APIError(ErrorCode.PROTOCOL_IMPORT_CONFLICT)
                    continue
                decision = request.results.get(item.key)
                if decision:
                    omitted.append({"kind": "result", "key": item.key, **decision.model_dump()})
                    continue
                if source.key not in athlete_ids:
                    issues.append({"kind": "result", "key": item.key, "reason": "athlete_unresolved"})
                    continue
                event = events[item.event_key]
                data = official_data(item, event, source.model_dump(exclude={"results"}), draft.id, teams.get(source.team_key))
                identity = {"competition_id": cid, "athlete_id": athlete_ids[source.key],
                            "stroke": data.pop("stroke"), "distance": data.pop("distance")}
                row, outcome = await write_result(Result, data, identity, event, item.round, payload.mode, connection, request.result_ids.get(item.key))
                if row is None:
                    issues.append({"kind": "result", "key": item.key, "reason": outcome})
                else:
                    done_results.add(item.key)
                    counts["results_" + outcome] += 1
        for item in payload.relays:
            if item.key in done_relays:
                if item.key in request.relays:
                    raise APIError(ErrorCode.PROTOCOL_IMPORT_CONFLICT)
                continue
            decision = request.relays.get(item.key)
            if decision:
                omitted.append({"kind": "relay", "key": item.key, **decision.model_dump()})
                continue
            if any(leg.athlete_key not in athlete_ids for leg in item.legs):
                issues.append({"kind": "relay", "key": item.key, "reason": "athlete_unresolved"})
                continue
            event = events[item.event_key]
            data = official_data(item, event, {"name": item.name}, draft.id)
            data["metadata"]["protocol_import"]["composition_complete"] = len(item.legs) == item.relay_count
            identity = {"competition_id": cid, **{k: data.pop(k) for k in ("name", "stroke", "distance", "relay_count", "gender")}}
            # A changed composition is an update even when team time is unchanged.
            existing_relays = await RelayResult.filter(**identity).using_db(connection)
            selected_id = request.relay_ids.get(item.key)
            existing_relays = [r for r in existing_relays if
                (r.id == selected_id if selected_id is not None else
                 (r.metadata or {}).get("protocol_import", {}).get("event") == event_identity(event)
                 and (r.metadata or {}).get("protocol_import", {}).get("round") == item.round)]
            desired_legs = [(leg.order, athlete_ids[leg.athlete_key], str(FlexibleTime.validate(leg.result)) if leg.result else None) for leg in sorted(item.legs, key=lambda x: x.order)]
            composition_changed = False
            if len(existing_relays) == 1:
                old_legs = await RelayLeg.filter(relay_result_id=existing_relays[0].id).using_db(connection).order_by("order")
                composition_changed = [(leg.order, leg.athlete_id, str(leg.result) if leg.result else None) for leg in old_legs] != desired_legs
                if composition_changed and payload.mode == "append":
                    issues.append({"kind": "relay", "key": item.key, "reason": "existing_composition_differs"})
                    continue
            row, outcome = await write_result(RelayResult, data, identity, event, item.round, payload.mode, connection, request.relay_ids.get(item.key))
            if row is None:
                issues.append({"kind": "relay", "key": item.key, "reason": outcome})
                continue
            if outcome != "unchanged" or composition_changed:
                if outcome == "unchanged":
                    outcome = "updated"
                await RelayLeg.filter(relay_result_id=row.id).using_db(connection).delete()
                for leg in item.legs:
                    await RelayLeg.create(relay_result_id=row.id, athlete_id=athlete_ids[leg.athlete_key], order=leg.order,
                                          result=FlexibleTime.validate(leg.result) if leg.result else None, using_db=connection)
            done_relays.add(item.key)
            counts["relays_" + outcome] += 1
        for source in payload.athletes:
            if source.key not in athlete_ids:
                continue
            athlete = await Athlete.get(id=athlete_ids[source.key]).using_db(connection)
            current_rank = normalize_license(athlete.license)
            if current_rank in MANUAL_LICENSES:
                continue
            ranks = await Result.filter(athlete_id=athlete.id).using_db(connection).values_list("final_rank", flat=True)
            desired = source.license if source.license in MANUAL_LICENSES else highest_automatic_license([current_rank, source.license, *ranks])
            if desired is not None and athlete.license != desired:
                athlete.license = desired
                await athlete.save(using_db=connection, update_fields=["license"])
                counts["licenses_updated"] += 1
        partial = bool(issues or omitted)
        if payload.mode == "replace" and partial:
            raise APIError(ErrorCode.PROTOCOL_IMPORT_CONFLICT)
        if not partial:
            competition.last_processed_at = datetime.now(timezone.utc)
            await competition.save(using_db=connection, update_fields=["last_processed_at"])
        response = {"type": "partial" if partial else "finished", "import_id": str(draft.id),
                    "competition_id": cid, **counts, "athletes": athlete_ids,
                    "results_processed": len(done_results), "results_total": len(result_keys),
                    "relays_processed": len(done_relays), "relays_total": len(payload.relays),
                    "issues": issues, "omitted": omitted, "last_processed_at_updated": not partial}
        draft.stage = "partial" if partial else "finish"
        draft.state = {**draft.state, "finish_request": request_json, "effective_request": request.model_dump(mode="json"), "response": response, "counts": counts,
                       "athletes": athlete_ids, "teams": teams,
                       "done_results": sorted(done_results), "done_relays": sorted(done_relays)}
        await draft.save(using_db=connection)
        return response
