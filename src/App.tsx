"use client";

import { useCallback, useMemo, useState } from "react";
import type { Feature, Geometry } from "geojson";
import { UnitDetails } from "./components/UnitDetails";
import { filterUnits, type UnitPin } from "./lib/units";
import { BoundaryMap } from "./components/BoundaryMap";
import { DetailsPanel } from "./components/DetailsPanel";
import { useCouncilData } from "./hooks/useCouncilData";
import { downloadText, featureName, featuresToCsv, filterFeatures, uniqueScoutingDistricts } from "./lib/gis";
import type { LayerKey, SelectedFeature, VisibilityState } from "./types/gis";

const programOptions = [["All", "Council"], ["Pack", "Packs"], ["Troop", "Troops"], ["Crew", "Crews"], ["Post", "Posts"], ["Ship", "Ships"]] as const;

const layerLabels: Record<LayerKey, string> = {
  counties: "Counties",
  scouting: "Scouting districts",
  schools: "School districts",
};

export function App() {
  const { data, error } = useCouncilData();
  const [showUnits, setShowUnits] = useState(true);
  const [unitStatus, setUnitStatus] = useState("Active");
  const [unitProgram, setUnitProgram] = useState("All");
  const [unitDistrict, setUnitDistrict] = useState("All");
  const [selectedUnits, setSelectedUnits] = useState<UnitPin[]>([]);
  const [activeLayer, setActiveLayer] = useState<LayerKey>("schools");
  const [query, setQuery] = useState("");
  const [coverage, setCoverage] = useState<"All" | "Full" | "Partial">("All");
  const [minimumPercent, setMinimumPercent] = useState(0);
  const [selected, setSelected] = useState<SelectedFeature>(null);
  const [visibility, setVisibility] = useState<VisibilityState>({ counties: true, scouting: true, schoolDistricts: true, schoolPoints: true });
  const onSelect = useCallback((feature: SelectedFeature) => { setSelected(feature); setSelectedUnits([]); }, []);
  const onUnitSelect = useCallback((units: UnitPin[]) => { setSelectedUnits(units); setSelected(null); }, []);
  const filteredUnits = useMemo(() => data ? filterUnits(data.units.units, unitStatus, unitProgram, unitDistrict) : [], [data, unitStatus, unitProgram, unitDistrict]);

  const activeCollection = useMemo(() => {
    if (!data) return null;
    if (activeLayer === "counties") return data.counties;
    if (activeLayer === "scouting") {
      return { type: "FeatureCollection" as const, features: uniqueScoutingDistricts(data.scouting).map((item) => item.feature) };
    }
    return data.schoolDistricts;
  }, [activeLayer, data]);

  const filtered = useMemo(
    () => activeCollection ? filterFeatures(activeCollection, activeLayer, query, coverage, minimumPercent) : [],
    [activeCollection, activeLayer, query, coverage, minimumPercent],
  );

  const toggle = (key: keyof VisibilityState) => setVisibility((current) => ({ ...current, [key]: !current[key] }));
  const exportData = (format: "csv" | "geojson") => {
    if (!activeCollection) return;
    const base = `cac-${activeLayer}-filtered`;
    if (format === "csv") downloadText(`${base}.csv`, featuresToCsv(filtered), "text/csv;charset=utf-8");
    else downloadText(`${base}.geojson`, JSON.stringify({ type: "FeatureCollection", features: filtered }, null, 2), "application/geo+json");
  };

  if (error) return <main className="status-screen"><strong>Map data could not be loaded.</strong><span>{error}</span></main>;
  if (!data) return <main className="status-screen"><span className="loader" /><strong>Preparing council map…</strong></main>;

  const schoolCount = data.schoolPoints.features.length;
  const assignedCount = data.schoolPoints.features.filter((feature) => feature.properties?.scouting_district && feature.properties.scouting_district !== "Unassigned").length;
  const snapshotDate = new Date(data.manifest.generated_at).toLocaleDateString("en-US", { timeZone: "America/Chicago" });

  return (
    <div className="dashboard-shell">
      <aside className="sidebar" aria-label="Map navigation">
        <div className="brand">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={`${import.meta.env.BASE_URL}cac-logo.png`} alt="Scouting America Capitol Area Council" />
        </div>
        <nav>
          <a href="#overview" className="active">Overview</a>
          <a href="#interactive-map">Interactive map</a>
          <a href="#district-table">District table</a>
          <a href="#unit-directory">Scouting units</a>
          <a href="#sources">Sources</a>
          <a href="https://pbsargent.github.io/council-dashboard-summary/">Council dashboard</a>
        </nav>
        <a className="report-problem" href="mailto:scouting@imetpetersargent.com?subject=Council%20school%20atlas%20issue">Report a problem</a>
        <div className="sidebar-note"><span>School data through</span><strong>{data.manifest.school_data_at ? new Date(data.manifest.school_data_at).toLocaleDateString("en-US", { timeZone: "America/Chicago" }) : snapshotDate}</strong><span>Boundary snapshot: {snapshotDate}</span></div>
      </aside>

      <main className="dashboard-main">
        <header className="hero" id="overview">
          <div>
            <p className="eyebrow">Capitol Area Council (CAC)</p>
            <h1>Council School Atlas</h1>
            <p className="lede">Explore schools, school districts, and council geography across Central Texas.</p>
            <fieldset className="banner-program-filter">
              <legend>Scouting program</legend>
              <div>{programOptions.map(([value, label]) => <button type="button" key={value} aria-pressed={unitProgram === value} onClick={() => {setUnitProgram(value);setSelectedUnits([]);setShowUnits(true);}}>{label}</button>)}</div>
              <p>{unitProgram === "All" ? "Council view includes every unit program." : `${programOptions.find(([value]) => value === unitProgram)?.[1]} view.`} {filteredUnits.length} units match the current pin-status and district filters.</p>
            </fieldset>
          </div>
          <div className="hero-actions">
            <a className="hero-button" href="#interactive-map">Open interactive map</a>
            <button type="button" className="hero-button secondary" onClick={() => window.print()}>Print map</button>
          </div>
        </header>

        <section className="kpi-grid" aria-label="Map summary">
          <article className="kpi-card"><span>Mapped schools</span><strong>{schoolCount.toLocaleString()}</strong><small>Independent school locations</small></article>
          <article className="kpi-card"><span>School districts</span><strong>{data.schoolDistricts.features.length}</strong><small>Full and partial council coverage</small></article>
          <article className="kpi-card"><span>District assigned</span><strong>{assignedCount.toLocaleString()}</strong><small>Schools with a scouting district</small></article>
          <article className="kpi-card"><span>Council geography</span><strong>{data.manifest.counts.scouting_district_names}</strong><small>Scouting districts · 15 counties</small></article>
        </section>

        <section className="panel map-panel" id="interactive-map" aria-labelledby="map-title">
          <div className="panel-head">
            <div><p className="section-kicker">Council geographic atlas</p><h2 id="map-title">Interactive school and district map</h2></div>
            <p className="panel-guidance">Scroll to zoom. Zoom out or use “View full council” to restore the complete map. Select a school dot for its full information card.</p>
          </div>

          <div className="filter-ribbon">
            <div className="filter-group">
              <label htmlFor="active-layer">Browse layer</label>
              <select id="active-layer" value={activeLayer} onChange={(event) => { setActiveLayer(event.target.value as LayerKey); setSelected(null); }}>
                {Object.entries(layerLabels).map(([value, label]) => <option value={value} key={value}>{label}</option>)}
              </select>
            </div>
            <div className="filter-group grow">
              <label htmlFor="district-search">Search {layerLabels[activeLayer].toLowerCase()}</label>
              <input id="district-search" type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder={`Search ${layerLabels[activeLayer].toLowerCase()}…`} />
            </div>
            <fieldset className="layer-toggles">
              <legend>Visible layers</legend>
              {([
                ["counties", "Counties"], ["scouting", "Scouting"],
                ["schoolDistricts", "School districts"], ["schoolPoints", "Mapped schools"],
              ] as Array<[keyof VisibilityState, string]>).map(([key, label]) => (
                <label key={key}><input type="checkbox" checked={visibility[key]} onChange={() => toggle(key)} /><i className={`layer-symbol ${key}`} aria-hidden="true" />{label}</label>
              ))}
            </fieldset>
          </div>

          {activeLayer === "schools" && (
            <div className="school-filter-row">
              <span>Council coverage</span>
              <div className="segmented">
                {(["All", "Full", "Partial"] as const).map((value) => <button type="button" className={coverage === value ? "active" : ""} onClick={() => setCoverage(value)} key={value}>{value}</button>)}
              </div>
              <label htmlFor="minimum-percent">Minimum inside council <strong>{minimumPercent}%</strong></label>
              <input id="minimum-percent" type="range" min="0" max="100" step="5" value={minimumPercent} onChange={(event) => setMinimumPercent(Number(event.target.value))} />
            </div>
          )}

          <div className="unit-filters">
            <label><input type="checkbox" checked={showUnits} onChange={event => {setShowUnits(event.target.checked);setSelectedUnits([]);}} /> Scouting units <span className="unit-legend">◆</span></label>
            <label>Pin status <select value={unitStatus} onChange={event => {setUnitStatus(event.target.value);setSelectedUnits([]);}}>{["Active", "Inactive", "All"].map(v => <option key={v}>{v}</option>)}</select></label>
            <label>Unit district <select value={unitDistrict} onChange={event => {setUnitDistrict(event.target.value);setSelectedUnits([]);}}>{["All", ...[...new Set(data.units.units.map(u => u.district))].sort()].map(v => <option key={v}>{v}</option>)}</select></label>
            <span>{filteredUnits.length} units · {filteredUnits.filter(u => !u.coordinates).length} without map coordinates</span>
          </div>
          <div className="map-stage">
            <BoundaryMap selectedUnits={selectedUnits} units={filteredUnits} showUnits={showUnits} onUnitSelect={onUnitSelect} data={data} visibility={visibility} selected={selected} coverage={coverage} minimumPercent={minimumPercent} activeLayer={activeLayer} onSelect={onSelect} />
            <div className={`map-focus-badge ${activeLayer}`}><span>Focused layer</span><strong>{layerLabels[activeLayer]}</strong></div>
            {visibility.schoolPoints && <div className="school-marker-help"><i aria-hidden="true" />Select a school dot for details</div>}
            <UnitDetails units={selectedUnits} onClose={() => setSelectedUnits([])} />
            <DetailsPanel feature={selected} onClose={() => setSelected(null)} />
          </div>
        </section>

        <section className="panel table-panel" id="district-table" aria-labelledby="table-title">
          <div className="panel-head">
            <div><p className="section-kicker">Geographic reference</p><h2 id="table-title">{layerLabels[activeLayer]}</h2></div>
            <div className="panel-actions"><span className="count-pill">{filtered.length} shown</span><button type="button" onClick={() => exportData("csv")}>CSV</button><button type="button" onClick={() => exportData("geojson")}>GeoJSON</button></div>
          </div>
          <div className="table-wrap">
            <table><thead><tr><th>Name</th><th>Coverage / type</th><th>Counties or area</th><th /></tr></thead>
              <tbody>{filtered.map((feature: Feature<Geometry>, index) => {
                const props = feature.properties ?? {};
                return <tr key={`${featureName(feature, activeLayer)}-${index}`}>
                  <td><strong>{featureName(feature, activeLayer)}</strong>{props.district_number && <small>{String(props.district_number)}</small>}</td>
                  <td>{String(props.coverage ?? props.status ?? "Council county")}{props.pct_district_in_council != null && <small>{Number(props.pct_district_in_council).toFixed(1)}% inside council</small>}</td>
                  <td>{props.council_counties ? String(props.council_counties) : props.school_districts ? String(props.school_districts) : props.area_name ? String(props.area_name) : props.land_area_sq_km ? `${Number(props.land_area_sq_km).toLocaleString()} km²` : "—"}</td>
                  <td><button type="button" className="detail-link" onClick={() => onSelect(feature)}>View</button></td>
                </tr>;
              })}</tbody>
            </table>
          </div>
        </section>

        <section className="panel table-panel" id="unit-directory" aria-labelledby="unit-directory-title">
          <div className="panel-head"><div><p className="section-kicker">Scouting unit directory</p><h2 id="unit-directory-title">{filteredUnits.length} units match your filters</h2></div></div>
          <p className="unit-directory-note">PinDataReport snapshot imported {new Date(data.units.importedAt).toLocaleDateString("en-US", { timeZone: "America/Chicago" })}. Pin locations may differ from meeting locations. Pin status does not confirm registration. Waterloo and Exploring are included as unit categories.</p>
          <div className="table-wrap"><table><thead><tr><th>Unit</th><th>District</th><th>Pin status</th><th>Location</th><th /></tr></thead><tbody>{filteredUnits.map(unit => <tr key={unit.id}><td><strong>{unit.name}</strong><small>{unit.program}</small></td><td>{unit.district}</td><td>{unit.pinStatus}{unit.updatedWithinYear === "No" && <small>Not updated within a year</small>}</td><td>{unit.coordinates ? "Mapped pin" : "Coordinates unavailable"}</td><td><button type="button" className="detail-link" onClick={() => {onUnitSelect([unit]);document.getElementById("interactive-map")?.scrollIntoView({behavior:"smooth"});}}>View</button></td></tr>)}</tbody></table></div>
        </section>
        <footer id="sources"><span>Prepared for Capitol Area Council planning</span><span>County geometry: U.S. Census 2025 · School districts: SY 2025–26 · Schools and scouting regions: CAC Schools snapshot · Units: Council PinDataReport</span></footer>
      </main>
    </div>
  );
}
