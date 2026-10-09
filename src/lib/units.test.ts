import { readFileSync } from "node:fs";
import { booleanPointInPolygon } from "@turf/turf";
import { describe, expect, it } from "vitest";
import { filterUnits, groupUnitPins, type UnitPayload } from "./units";
const payload: UnitPayload = JSON.parse(readFileSync(new URL("../../public/data/unit-pins.json", import.meta.url), "utf8"));
describe("unit pins", () => {
  it("preserves unique units and excludes private contacts", () => {
    expect(payload.units).toHaveLength(296);
    expect(new Set(payload.units.map(u => u.id)).size).toBe(296);
    expect(JSON.stringify(payload)).not.toMatch(/primarycontact|alternatecontact|contactemail|contactphone/i);
  });
  it("filters active pins and preserves units without coordinates in the directory", () => {
    const active = filterUnits(payload.units, "Active", "All", "All");
    expect(active).toHaveLength(266);
    expect(active.filter(u => !u.coordinates)).toHaveLength(3);
    expect(filterUnits(active, "Active", "Pack", "Armadillo 02").every(u => u.program === "Pack" && u.district === "Armadillo 02")).toBe(true);
  });
  it("groups shared coordinates without losing units", () => {
    const groups = groupUnitPins(payload.units);
    expect(groups.flat()).toHaveLength(293);
    expect(Math.max(...groups.map(g => g.length))).toBe(16);
    const council = JSON.parse(readFileSync(new URL("../../public/data/CapitolAreaCouncil.geojson", import.meta.url), "utf8"));
    expect(groups.flat().every(u => booleanPointInPolygon(u.coordinates!, council.features[0]))).toBe(true);
  });
});
