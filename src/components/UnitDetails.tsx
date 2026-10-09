import { normalizeWebsite } from "../lib/display";
import type { UnitPin } from "../lib/units";
export function UnitDetails({ units, onClose }: { units: UnitPin[]; onClose: () => void }) {
  if (!units.length) return null;
  return <aside className="details-panel unit-details" aria-live="polite" aria-label="Selected Scouting units">
    <div className="details-heading"><div><p className="section-kicker">Scouting units</p><h2>{units.length > 1 ? `${units.length} units share this pin` : units[0].name}</h2></div><button type="button" className="icon-button" aria-label="Close unit information" onClick={onClose}>×</button></div>
    <p className="unit-caveat">Locations represent mapped pins; they may differ from meeting locations. Active refers to pin status, not registration.</p>
    {units.map(unit => {
      const website = normalizeWebsite(unit.website);
      return <section className="card-section" key={unit.id}><h3>{unit.name}</h3><dl className="generic-details">
        <div><dt>Program / district</dt><dd>{unit.program} · {unit.district}</dd></div>
        <div><dt>Pin status / view</dt><dd>{unit.pinStatus} · {unit.pinView}</dd></div>
        <div><dt>Applications</dt><dd>{unit.applicationStatus}</dd></div>
        <div><dt>Pin address</dt><dd>{unit.pinAddress || "Unavailable"}</dd></div>
        <div><dt>Meeting address</dt><dd>{unit.meetingAddress || "Unavailable"}</dd></div>
        <div><dt>Meeting schedule</dt><dd>{[unit.meetingSchedule, unit.meetingWeek, unit.meetingDay, unit.meetingStart && `${unit.meetingStart}–${unit.meetingEnd || "?"}`].filter(Boolean).join(" · ") || "Not provided"}</dd></div>
        {website && <div><dt>Website</dt><dd><a href={website} target="_blank" rel="noreferrer">Open unit website</a></dd></div>}
        <div><dt>Last modified</dt><dd>{unit.lastModified || "Unavailable"}{unit.updatedWithinYear === "No" ? " · Not updated within a year" : ""}</dd></div>
        {!unit.coordinates && <div><dt>Location</dt><dd>No usable coordinates; listed in directory only.</dd></div>}
      </dl></section>;
    })}
  </aside>;
}
