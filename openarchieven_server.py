#!/usr/bin/env python3
import requests
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP

# -------------------------------------------------------
# MCP SERVER INITIALIZATION
# -------------------------------------------------------

mcp = FastMCP("openarchieven")

# API base URLs (versioned, per official docs)
BASE_1_1 = "https://api.openarchieven.nl/1.1/"
BASE_1_0 = "https://api.openarchieven.nl/1.0/"


# -------------------------------------------------------
# INTERNAL HELPERS
# -------------------------------------------------------

def safe_get(url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    HTTP GET with robust error handling.

    Returns:
        {"ok": True, "data": <parsed_json>}
    or:
        {"ok": False, "error": <code>, "details": {...}}
    """
    try:
        resp = requests.get(url, params=params, timeout=20)
    except Exception as e:
        return {
            "ok": False,
            "error": "connection_error",
            "details": {"url": url, "params": params, "message": str(e)},
        }

    if not resp.ok:
        return {
            "ok": False,
            "error": "http_error",
            "details": {
                "url": url,
                "params": params,
                "status_code": resp.status_code,
                "body": resp.text[:2000],
            },
        }

    try:
        data = resp.json()
    except Exception:
        return {
            "ok": False,
            "error": "invalid_json",
            "details": {
                "url": url,
                "params": params,
                "body": resp.text[:2000],
            },
        }

    return {"ok": True, "data": data}


def normalize_search_docs(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize /records/search.json docs into LLM-friendly fields.
    """
    normalized: List[Dict[str, Any]] = []
    for d in docs:
        eventdate = d.get("eventdate") or {}
        year = eventdate.get("year") if isinstance(eventdate, dict) else None
        norm = {
            "pid": d.get("pid"),
            "identifier": d.get("identifier"),
            "name": d.get("personname") or d.get("name"),
            "relation_type": d.get("relationtype"),
            "event_type": d.get("eventtype"),
            "event_year": year,
            "event_place": d.get("eventplace"),
            "archive_code": d.get("archive_code"),
            "archive": d.get("archive"),
            "source_type": d.get("sourcetype"),
            "url": d.get("url"),
        }
        normalized.append(norm)
    return normalized


def build_error_result(err: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standard wrapper to expose safe_get errors to the agent.
    """
    return {
        "status": "error",
        "error": err.get("error"),
        "details": err.get("details"),
    }


# -------------------------------------------------------
# TOOLS
# -------------------------------------------------------

@mcp.tool()
def search_people(
    name: str,
    archive_code: str = "",
    number_show: int = 10,
    sourcetype: str = "",
    eventplace: str = "",
    relationtype: str = "",
    country_code: str = "",
    sort: int = 1,
    lang: str = "en",
    start: int = 0,
) -> Dict[str, Any]:
    """
    Search for persons and events across Open Archieven.
    """
    if not name.strip():
        return {
            "status": "error",
            "error": "missing_name",
            "details": {"message": "Parameter 'name' is required."},
        }

    params: Dict[str, Any] = {
        "name": name,
        "number_show": number_show,
        "start": start,
        "sort": sort,
        "lang": lang,
    }
    if archive_code:
        params["archive_code"] = archive_code
    if sourcetype:
        params["sourcetype"] = sourcetype
    if eventplace:
        params["eventplace"] = eventplace
    if relationtype:
        params["relationtype"] = relationtype
    if country_code:
        params["country_code"] = country_code

    result = safe_get(BASE_1_1 + "records/search.json", params)
    if not result["ok"]:
        return build_error_result(result)

    raw = result["data"]
    query = raw.get("query", {})
    response = raw.get("response", {})
    docs = response.get("docs", []) or []

    return {
        "status": "ok",
        "raw": raw,
        "normalized": {
            "query": query,
            "total_found": response.get("number_found"),
            "people": normalize_search_docs(docs),
        },
    }


@mcp.tool()
def search_people_all(
    name: str,
    archive_code: str = "",
    sourcetype: str = "",
    eventplace: str = "",
    relationtype: str = "",
    country_code: str = "",
    sort: int = 1,
    lang: str = "en",
    page_size: int = 100,
) -> Dict[str, Any]:
    """
    Fetch all pages of search results for a person query.
    """
    if page_size <= 0 or page_size > 100:
        page_size = 100

    if not name.strip():
        return {
            "status": "error",
            "error": "missing_name",
            "details": {"message": "Parameter 'name' is required."},
        }

    start = 0
    all_docs: List[Dict[str, Any]] = []
    first_raw: Optional[Dict[str, Any]] = None
    query_obj: Dict[str, Any] = {}
    total_found: Optional[int] = None

    while True:
        params: Dict[str, Any] = {
            "name": name,
            "number_show": page_size,
            "start": start,
            "sort": sort,
            "lang": lang,
        }
        if archive_code:
            params["archive_code"] = archive_code
        if sourcetype:
            params["sourcetype"] = sourcetype
        if eventplace:
            params["eventplace"] = eventplace
        if relationtype:
            params["relationtype"] = relationtype
        if country_code:
            params["country_code"] = country_code

        result = safe_get(BASE_1_1 + "records/search.json", params)
        if not result["ok"]:
            return build_error_result(result)

        raw = result["data"]
        if first_raw is None:
            first_raw = raw
        query_obj = raw.get("query", {}) or query_obj
        response = raw.get("response", {})
        docs = response.get("docs", []) or []
        number_found = response.get("number_found")
        if total_found is None and isinstance(number_found, int):
            total_found = number_found

        if not docs:
            break

        all_docs.extend(docs)
        start += len(docs)
        if isinstance(total_found, int) and start >= total_found:
            break

    return {
        "status": "ok",
        "raw": first_raw,
        "normalized": {
            "query": query_obj,
            "total_found": total_found if total_found is not None else len(all_docs),
            "people": normalize_search_docs(all_docs),
        },
    }


@mcp.tool()
def match_person(
    name: str,
    birthyear: int,
    lang: str = "en",
) -> Dict[str, Any]:
    """
    Exact match search by name + birthyear.
    """
    if not name.strip():
        return {
            "status": "error",
            "error": "missing_name",
            "details": {"message": "Parameter 'name' is required."},
        }

    params: Dict[str, Any] = {"name": name, "birthyear": birthyear, "lang": lang}
    result = safe_get(BASE_1_0 + "records/match.json", params)
    if not result["ok"]:
        return build_error_result(result)

    raw = result["data"]
    query = raw.get("query", {})
    response = raw.get("response", {})
    docs = response.get("docs", []) or []

    normalized_matches: List[Dict[str, Any]] = []
    for d in docs:
        normalized_matches.append(
            {
                "uri": d.get("uri"),
                "archive_code": d.get("archive_code"),
                "archive": d.get("archive"),
                "event_type": d.get("eventtype"),
                "event_place": d.get("eventplace"),
                "source_type": d.get("sourcetype"),
            }
        )

    return {
        "status": "ok",
        "raw": raw,
        "normalized": {
            "query": query,
            "total_found": response.get("number_found"),
            "matches": normalized_matches,
        },
    }


def _build_person_display_name(person: Dict[str, Any]) -> Optional[str]:
    """
    Build a human-readable name from the A2A Person structure.
    """
    pn = person.get("PersonName") or {}
    if not isinstance(pn, dict):
        return None
    first = pn.get("PersonNameFirstName")
    prefix = pn.get("PersonNamePrefixLastName")
    last = pn.get("PersonNameLastName")
    parts: List[str] = []
    if first:
        parts.append(first)
    if prefix:
        parts.append(prefix)
    if last:
        parts.append(last)
    return " ".join(parts) if parts else None


@mcp.tool()
def get_record_details(
    archive: str,
    identifier: str,
    lang: str = "en",
) -> Dict[str, Any]:
    """
    Get the full genealogical record (A2A JSON).
    """
    if not archive.strip() or not identifier.strip():
        return {
            "status": "error",
            "error": "missing_parameters",
            "details": {
                "message": "Both 'archive' and 'identifier' are required.",
            },
        }

    params = {"archive": archive, "identifier": identifier, "lang": lang}
    result = safe_get(BASE_1_1 + "records/show.json", params)
    if not result["ok"]:
        return build_error_result(result)

    raw = result["data"]

    # Persons
    persons_raw = raw.get("Person", []) or []
    persons_norm: List[Dict[str, Any]] = []
    if isinstance(persons_raw, list):
        for p in persons_raw:
            if not isinstance(p, dict):
                continue
            display_name = _build_person_display_name(p)
            persons_norm.append(
                {
                    "pid": p.get("@pid") or p.get("pid"),
                    "name": display_name,
                }
            )

    # Event
    event_raw = raw.get("Event", {}) or {}
    event_norm: Dict[str, Any] = {}
    if isinstance(event_raw, dict):
        ev_date = event_raw.get("EventDate") or {}
        ev_place = event_raw.get("EventPlace") or {}
        literal_date = ev_date.get("LiteralDate")
        year = ev_date.get("Year")
        month = ev_date.get("Month")
        day = ev_date.get("Day")
        event_norm = {
            "type": event_raw.get("EventType"),
            "literal_date": literal_date,
            "year": year,
            "month": month,
            "day": day,
            "place": ev_place.get("Place"),
        }

    # Source
    source_raw = raw.get("Source", {}) or {}
    source_norm: Dict[str, Any] = {}
    if isinstance(source_raw, dict):
        src_place = source_raw.get("SourcePlace") or {}
        src_ref = source_raw.get("SourceReference") or {}
        source_norm = {
            "type": source_raw.get("SourceType"),
            "place": src_place.get("Place"),
            "country": src_place.get("Country"),
            "institution_name": src_ref.get("InstitutionName"),
            "collection": src_ref.get("Collection"),
            "book": src_ref.get("Book"),
            "registry_number": src_ref.get("RegistryNumber"),
            "document_number": src_ref.get("DocumentNumber"),
        }

    return {
        "status": "ok",
        "raw": raw,
        "normalized": {
            "persons": persons_norm,
            "event": event_norm,
            "source": source_norm,
        },
    }


@mcp.tool()
def get_births_years_ago(
    years: int,
    number_show: int = 10,
) -> Dict[str, Any]:
    """
    Get list of births that occurred N years ago (from today).
    """
    if years <= 0:
        return {
            "status": "error",
            "error": "invalid_years",
            "details": {"message": "'years' must be a positive integer."},
        }

    params = {"years": years, "number_show": number_show}
    result = safe_get(BASE_1_1 + "records/yearsago.json", params)
    if not result["ok"]:
        return build_error_result(result)

    raw = result["data"]
    items = raw if isinstance(raw, list) else []

    normalized_births: List[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        normalized_births.append(
            {
                "archive_code": item.get("archive_code"),
                "archive": item.get("archive"),
                "identifier": item.get("identifier"),
                "name": item.get("name"),
                "place": item.get("place"),
                "has_scan": bool(item.get("scan")),
                "url": item.get("url"),
            }
        )

    return {
        "status": "ok",
        "raw": raw,
        "normalized": {
            "years": years,
            "count": len(normalized_births),
            "births": normalized_births,
        },
    }


@mcp.tool()
def get_census_data(
    year: int,
    place: str = "",
    gg_uri: str = "",
    province: str = "",
    richness: int = 1,
) -> Dict[str, Any]:
    """
    Get census data for a Dutch place/municipality nearest to a year.
    """
    if year < 1770 or year > 1980:
        return {
            "status": "error",
            "error": "invalid_year",
            "details": {
                "message": "Year must be between 1770 and 1980 (inclusive).",
            },
        }

    if not gg_uri and not place:
        return {
            "status": "error",
            "error": "missing_place_or_gg_uri",
            "details": {
                "message": "Either 'place' or 'gg_uri' is required.",
            },
        }

    params: Dict[str, Any] = {
        "year": year,
        "richness": richness,
    }
    if gg_uri:
        params["gg_uri"] = gg_uri
    else:
        params["place"] = place
    if province:
        params["province"] = province

    result = safe_get(BASE_1_0 + "related/census.json", params)
    if not result["ok"]:
        return build_error_result(result)

    raw = result["data"]
    census_entries = raw.get("census", []) if isinstance(raw, dict) else []
    totals = raw.get("totals", {}) if isinstance(raw, dict) else {}

    normalized_census: List[Dict[str, Any]] = []
    for c in census_entries:
        if not isinstance(c, dict):
            continue
        normalized_census.append(
            {
                "name": c.get("name"),
                "year": c.get("year"),
                "province": c.get("province"),
                "population": c.get("population"),
                "gg_uri": c.get("gg_uri"),
                "table": c.get("table"),
            }
        )

    return {
        "status": "ok",
        "raw": raw,
        "normalized": {
            "year": year,
            "entries": normalized_census,
            "totals_by_province": totals,
        },
    }


@mcp.tool()
def list_comments(
    archive: str = "",
    number_show: int = 10,
    since: str = "",
) -> Dict[str, Any]:
    """
    List approved comments made on records.
    """
    params: Dict[str, Any] = {"number_show": number_show}
    if archive:
        params["archive"] = archive
    if since:
        params["since"] = since

    result = safe_get(BASE_1_0 + "comments/list.json", params)
    if not result["ok"]:
        return build_error_result(result)

    raw = result["data"]
    comments = raw if isinstance(raw, list) else []

    normalized_comments: List[Dict[str, Any]] = []
    for c in comments:
        if not isinstance(c, dict):
            continue
        normalized_comments.append(
            {
                "id": c.get("id"),
                "identifier": c.get("identifier"),
                "archive": c.get("archive"),
                "author_name": c.get("name"),
                "comment": c.get("comment"),
                "created": c.get("created"),
            }
        )

    return {
        "status": "ok",
        "raw": raw,
        "normalized": {
            "count": len(normalized_comments),
            "comments": normalized_comments,
        },
    }


# -------------------------------------------------------
# ASGI APP FOR UVICORN (Streamable HTTP)
# -------------------------------------------------------

app = mcp.streamable_http_app()
