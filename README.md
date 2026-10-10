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
