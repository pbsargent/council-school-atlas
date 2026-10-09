import type { Map as MapLibreMap } from "maplibre-gl";
import { groupUnitPins, type UnitPin } from "../lib/units";

export function UnitOverlay({ map, units, revision, onSelect }: { map: MapLibreMap; units: UnitPin[]; revision: number; onSelect: (units: UnitPin[]) => void }) {
  return <div className="unit-pin-layer" data-map-revision={revision}>
    {groupUnitPins(units).map(group => {
      const point = map.project(group[0].coordinates!);
      const label = group.length > 1 ? `${group.length} units at this pin: ${group.map(u => u.name).join(", ")}` : group[0].name;
      return <button key={group[0].coordinates!.join(",")} type="button" className={`unit-pin ${group.length > 1 ? "grouped" : ""}`} style={{left:point.x,top:point.y}} title={label} aria-label={label} onClick={event => {event.stopPropagation();onSelect(group);}}>{group.length > 1 ? group.length : "◆"}</button>;
    })}
  </div>;
}
