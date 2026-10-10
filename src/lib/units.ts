import { booleanPointInPolygon } from "@turf/turf";
import type { Feature, Geometry } from "geojson";

export type UnitPin = {
  id: string; name: string; program: string; district: string;
  pinStatus: string; pinView: string; applicationStatus: string;
  coordinates: [number, number] | null;
  pinAddress: string; meetingAddress: string; meetingSchedule: string;
  meetingWeek: string; meetingDay: string; meetingStart: string; meetingEnd: string;
  coordinatesRetained?: boolean;
  zipCode?: string | null;
  beascoutUrl?: string | null;
  beascoutVerifiedAt?: string | null;
  website: string; updatedWithinYear: string; lastModified: string;
};
export type UnitPayload = { source: string; importedAt: string; units: UnitPin[] };
export function filterUnits(units: UnitPin[], status: string, program: string, district: string, districtQuery = "") {
  const query = districtQuery.trim().toLocaleLowerCase();
  return units.filter(u => (status === "All" || u.pinStatus === status) && (program === "All" || u.program === program) && (district === "All" || u.district === district) && (!query || u.district.toLocaleLowerCase().includes(query)));
}
export function filterUnitsByBoundaries(units: UnitPin[], boundaries: Feature<Geometry>[]) {
  return units.filter(unit => unit.coordinates && boundaries.some(boundary =>
    (boundary.geometry.type === "Polygon" || boundary.geometry.type === "MultiPolygon") &&
    booleanPointInPolygon(unit.coordinates!, boundary as Feature<import("geojson").Polygon | import("geojson").MultiPolygon>)
  ));
}
export function groupUnitPins(units: UnitPin[]) {
  const groups = new Map<string, UnitPin[]>();
  for (const unit of units) {
    if (!unit.coordinates) continue;
    const key = unit.coordinates.join(",");
    groups.set(key, [...(groups.get(key) ?? []), unit]);
  }
  return [...groups.values()];
}
