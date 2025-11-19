# Normalization Strategy

Each MCP tool returns two layers of data:

- `raw` – the original JSON as returned by the OpenArchieven API
- `normalized` – a simplified, LLM-oriented view with consistent keys

This approach balances:

- **Traceability** – the API payload is always available for advanced logic
- **Usability** – agents can work primarily with normalized data structures

---

## `search_people` / `search_people_all`

**raw**

Direct OpenArchieven structure, e.g.:

- `query`
- `response.number_found`
- `response.docs[]`

**normalized**

```json
{
  "query": { ... },
  "total_found": 123,
  "people": [
    {
      "pid": "...",
      "identifier": "...",
      "name": "...",
      "relation_type": "...",
      "event_type": "...",
      "event_year": 1850,
      "event_place": "...",
      "archive_code": "...",
      "archive": "...",
      "source_type": "...",
      "url": "..."
    }
  ]
}
```

Reasoning:

- `people[]` is a flat list with the most important attributes for matching and ranking.
- The agent avoids parsing deeply nested or archive-specific fields.

---

## `match_person`

**raw**

- Contains `query` and `response.docs`.

**normalized**

```json
{
  "query": { ... },
  "total_found": 5,
  "matches": [
    {
      "uri": "...",
      "archive_code": "...",
      "archive": "...",
      "event_type": "...",
      "event_place": "...",
      "source_type": "..."
    }
  ]
}
```

Reasoning:

- The agent can quickly see which archives and event types match a name + year.

---

## `get_record_details`

**raw**

- Full A2A record structure:
  - `Person[]`
  - `Event`
  - `Source`

**normalized**

```json
{
  "persons": [
    {
      "pid": "P1",
      "name": "Firstname Prefix Lastname"
    }
  ],
  "event": {
    "type": "Birth",
    "literal_date": "12-03-1850",
    "year": 1850,
    "month": 3,
    "day": 12,
    "place": "Amsterdam"
  },
  "source": {
    "type": "...",
    "place": "...",
    "country": "...",
    "institution_name": "...",
    "collection": "...",
    "book": "...",
    "registry_number": "...",
    "document_number": "..."
  }
}
```

Reasoning:

- Most genealogical tasks need the main persons, event date/place, and source reference.
- The full A2A model is still available if needed via `raw`.

---

## `get_births_years_ago`

**normalized**

```json
{
  "years": 200,
  "count": 10,
  "births": [
    {
      "archive_code": "hco",
      "archive": "Historisch Centrum Overijssel",
      "identifier": "...",
      "name": "...",
      "place": "...",
      "has_scan": true,
      "url": "..."
    }
  ]
}
```

Reasoning:

- Simple list to surface historically interesting people for a given anniversary.

---

## `get_census_data`

**normalized**

```json
{
  "year": 1840,
  "entries": [
    {
      "name": "Leiden",
      "year": 1840,
      "province": "Zuid-Holland",
      "population": 37464,
      "gg_uri": "http://www.gemeentegeschiedenis.nl/...",
      "table": {
        "02 huizen": 6300,
        "03 huisgezinnen": 7859,
        ...
      }
    }
  ],
  "totals_by_province": {
    "Zuid-Holland": 526020,
    "Noord-Holland": 443334,
    ...
  }
}
```

Reasoning:

- Provides both city-level and province-level context in a consistent shape.

---

## `list_comments`

**normalized**

```json
{
  "count": 3,
  "comments": [
    {
      "id": "986865669",
      "identifier": "1ab53c35-8f00-4208-d75e-eba4d0bef198",
      "archive": "elo",
      "author_name": "coret",
      "comment": "Some comment text...",
      "created": "2013-08-03 09:41:05"
    }
  ]
}
```

Reasoning:

- Gives agents a clear list of user-generated notes that can be attached to records or used as hints.
