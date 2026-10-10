import { readFileSync } from "node:fs";
import { booleanPointInPolygon } from "@turf/turf";
import { describe, expect, it } from "vitest";
import { filterUnits, groupUnitPins, type UnitPayload } from "./units";
const payload: UnitPayload = JSON.parse(readFileSync(new URL("../../public/data/unit-pins.json", import.meta.url), "utf8"));
describe("unit pins", () => {
  it("preserves unique units and excludes private contacts", () => {
    expect(payload.units.length).toBeGreaterThan(0);
    expect(new Set(payload.units.map(u => u.id)).size).toBe(payload.units.length);
    expect(JSON.stringify(payload)).not.toMatch(/primarycontact|alternatecontact|contactemail|contactphone/i);
  });
  it("filters active pins and preserves units without coordinates in the directory", () => {
    const active = filterUnits(payload.units, "Active", "All", "All");
    expect(active).toEqual(payload.units.filter(u => u.pinStatus === "Active"));
    expect(active.filter(u => !u.coordinates)).toEqual(payload.units.filter(u => u.pinStatus === "Active" && !u.coordinates));
    expect(filterUnits(active, "Active", "Pack", "Armadillo 02").every(u => u.program === "Pack" && u.district === "Armadillo 02")).toBe(true);
  });
  it("applies scouting district search together with program, status and district filters", () => {
    const expected = payload.units.filter(u => u.pinStatus === "Active" && u.program === "Pack" && /armadillo/i.test(u.district));
    expect(expected.length).toBeGreaterThan(0);
    expect(filterUnits(payload.units, "Active", "Pack", "All", "  ARMADILLO ")).toEqual(expected);
    expect(filterUnits(payload.units, "Active", "Pack", "Bee Cave 01", "Armadillo")).toEqual([]);
    expect(filterUnits(payload.units, "All", "All", "All", "no such district")).toEqual([]);
    expect(filterUnits(payload.units, "All", "All", "All", "")).toEqual(payload.units);
  });
  it("uses only verified canonical BeAScout unit pages", () => {
    const linked = payload.units.filter(u => u.beascoutUrl);
    expect(linked.every(u => /^https:\/\/beascout\.scouting\.org\/units\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(u.beascoutUrl!) && Boolean(u.beascoutVerifiedAt))).toBe(true);
    expect(new Set(linked.map(u => u.beascoutUrl)).size).toBe(linked.length);
  });
  it("groups shared coordinates without losing units", () => {
    const groups = groupUnitPins(payload.units);
    expect(groups.flat()).toHaveLength(payload.units.filter(u => u.coordinates).length);
    expect(new Set(groups.flat().map(u => u.id)).size).toBe(groups.flat().length);
    const council = JSON.parse(readFileSync(new URL("../../public/data/CapitolAreaCouncil.geojson", import.meta.url), "utf8"));
    expect(groups.flat().every(u => booleanPointInPolygon(u.coordinates!, council.features[0]))).toBe(true);
  });
});
