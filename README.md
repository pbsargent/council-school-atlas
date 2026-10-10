# Council School Atlas

Independent local copy of the council map with all Join Scout Night tracking removed. Includes school locations, contacts, county boundaries, school districts, derived scouting regions, geographic filters, printing, and CSV/GeoJSON exports.

No event dates, recruitment statuses, approvals, youth-talk dates, staff leads, or assigned units are stored or loaded. The school-directory snapshot is in `data/school-directory.json`; the app loads only `public/data` GeoJSON and its manifest. There is no live Monday connection or JSN refresh/publishing automation in this copy.

Existing school locations and scouting-region assignments retain CAC Schools snapshot provenance. This is not a complete NCES school inventory. Derived scouting regions are planning aids, not legal boundaries. The geographic snapshot date and school-directory extraction date are recorded separately in their source files.

Sources: OpenStreetMap basemap; U.S. Census 2025 county boundaries; Texas Education Agency / Texas Legislative Council school districts SY 2025–26; preserved CAC Schools directory and assignments.

Run `pnpm dev`, `pnpm typecheck`, `pnpm test`, `pnpm build`, or `pnpm build:github`. The static build uses `/council-school-atlas/` as its base. The GitHub Pages workflow builds and deploys pushes to main.

To regenerate GIS, run `pnpm data:build` with `SCHOOL_DISTRICT_SHP`, `SCHOOL_DISTRICT_CSV`, and `COUNTY_SHP` pointing to the original GIS inputs. The build reads the sanitized school directory and CAC Schools assignment snapshot.

## Scouting units overlay

The optional blue unit overlay defaults to Active pin status, with program and unit-district filters. Shared coordinates use grouped markers listing every matching unit. A filtered directory retains units without coordinates. Cards separate pin and meeting addresses, show meeting information and website links, and flag records marked not updated within a year. Active pin status is not registration status. Waterloo and Exploring appear as unit categories, without new boundary polygons.

Refresh the snapshot with `python3 scripts/import-unit-pins.py [path-to-PinDataReport.csv]`, then rebuild. Import uses Windows-1252 encoding and an explicit field allowlist; personal contact names, email addresses and phone numbers are excluded. The original report is read without modification. No recurring refresh is configured.

The interface uses the Council Dashboard’s CAC theme palette: navy #051f4c, blue #2c7ff8, green #9cba3b, gold #f6b227, red #ef4923, with matching light/dark surfaces and navy topographic imagery.

Live site: https://pbsargent.github.io/council-school-atlas/

Refresh school details with `python3 scripts/refresh-school-snapshot.py [monday_map_source.json]`. This verifies source identities and column/group completeness, joins mapped schools by item ID, preserves nulls and coordinates, and leaves the assignment-derived region snapshot unchanged. School and boundary dates are shown separately.

## Weekly refresh safeguards

Use `python3 scripts/weekly-atlas-refresh.py check` on Monday. It validates recent, complete school and unit files and compares counts with the live published site. If unchanged, do not write or publish. If changed, use `prepare` from a clean checkout; it locks against concurrent runs, stages both sources, validates them before replacement, and records the candidate under ignored `.atlas-refresh/`. School joins use item identity, preserve nulls and known geometry, remove deleted source IDs, and add Independent schools only with a unique verified in-council location. Unlocated schools remain explicit warnings. Region polygons retain their own snapshot date. Unit imports reject duplicate IDs, malformed rows, invalid statuses and corrupt coordinates; missing coordinates retain a prior verified pin with a visible warning. Personal contact fields are never imported.

Before pushing, run Python refresh tests, typecheck, lint, application tests, and both production builds with bundled ARM64 Node. Review changed counts and warnings, commit only intended atlas changes, and wait for GitHub Pages. Run `python3 scripts/weekly-atlas-refresh.py verify` afterward: the full live manifest and unit payload must match local candidate data before a successful-publication receipt is written. The live site remains the count baseline if build, push, deployment or verification fails. Never replace a failed publication with a success report.

Source recency validation is seven days; a stale or future-dated file requires attention, rather than an invented count change. This checks file evidence and required payloads; it cannot prove the upstream exporter delivered every record. Investigate unexpected count drops against its retrieval audit before publication.

## Unit-specific BeAScout links

Read `docs/BEASCOUT_DIRECT_LINK_RULES.md`. ZIP5 and numeric internal unit IDs come from PinDataReport. `python3 scripts/resolve-beascout-links.py` follows the public resolver at modest concurrency, requires HTTP 200 and a canonical `/units/UUID` URL, and verifies the exact legacy unit ID in the returned unit payload. Contradictory program/number identities are rejected. A lower-concurrency second pass retries unresolved requests. Verified links display in unit cards; failures retain existing canonical links or remain omitted. An audit is saved under ignored `.atlas-refresh/beascout-link-audit.json`, and written links are read back. The weekly staged refresh also runs this resolver whenever a count change triggers a refresh.
