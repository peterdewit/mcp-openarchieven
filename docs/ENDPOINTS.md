# OpenArchieven JSON Endpoints

This MCP server uses the JSON endpoints from OpenArchieven API versions 1.0 and 1.1.

Only `.json` endpoints are implemented. Other formats (XML, TTL, GEDCOM, NT) are deliberately excluded.

---

## 1. Person Search – `/1.1/records/search.json`

Search for persons/events by name and optional filters.

**HTTP**

- Method: `GET`
- URL: `https://api.openarchieven.nl/1.1/records/search.json`

**Parameters**

- `name` (string, required) – search term, usually a full name
- `archive_code` (string, optional) – restrict to one archive
- `number_show` (int, optional, default 10, max 100) – results per page
- `sourcetype` (string, optional) – filter by source type
- `eventplace` (string, optional) – filter by event place
- `relationtype` (string, optional) – filter by relation type
- `country_code` (string, optional) – filter by country
- `sort` (int, optional, default 1) – sort order
- `lang` (string, optional, default `"en"`) – language
- `start` (int, optional, default 0) – offset for paging

**Mapped tool**

- `search_people`
- `search_people_all` (paging loop using `start` and `number_show`)

---

## 2. Exact Match – `/1.0/records/match.json`

Exact/close matches using name + birth year.

**HTTP**

- Method: `GET`
- URL: `https://api.openarchieven.nl/1.0/records/match.json`

**Parameters**

- `name` (string, required)
- `birthyear` (int, required)
- `lang` (string, optional)

**Mapped tool**

- `match_person`

---

## 3. Record Details – `/1.1/records/show.json`

Fetch a complete genealogical record (A2A JSON) for a specific archive + identifier.

**HTTP**

- Method: `GET`
- URL: `https://api.openarchieven.nl/1.1/records/show.json`

**Parameters**

- `archive` (string, required) – archive code
- `identifier` (string, required) – record identifier
- `lang` (string, optional)

**Mapped tool**

- `get_record_details`

---

## 4. Births X Years Ago – `/1.1/records/yearsago.json`

List people born a given number of years ago from today.

**HTTP**

- Method: `GET`
- URL: `https://api.openarchieven.nl/1.1/records/yearsago.json`

**Parameters**

- `years` (int, required) – number of years ago
- `number_show` (int, optional, default 10) – maximum persons returned

**Mapped tool**

- `get_births_years_ago`

---

## 5. Related Census – `/1.0/related/census.json`

Retrieve census data for a Dutch place/municipality near a given year.

**HTTP**

- Method: `GET`
- URL: `https://api.openarchieven.nl/1.0/related/census.json`

**Parameters**

- `year` (int, required) – between 1770 and 1980
- `place` (string, required if `gg_uri` not provided)
- `gg_uri` (string, required if `place` not provided)
- `province` (string, optional)
- `richness` (int, optional, default 1; higher = more detail)

**Mapped tool**

- `get_census_data`

---

## 6. Comments List – `/1.0/comments/list.json`

List approved user comments on records.

**HTTP**

- Method: `GET`
- URL: `https://api.openarchieven.nl/1.0/comments/list.json`

**Parameters**

- `archive` (string, optional) – filter by archive
- `number_show` (int, optional, default 10, max 100)
- `since` (string, optional) – filter by creation date

**Mapped tool**

- `list_comments`
