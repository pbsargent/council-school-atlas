"use client";

import { useEffect, useState } from "react";
import type { CouncilData } from "../types/gis";

const dataPath = (fileName: string) => `${import.meta.env.BASE_URL}data/${fileName}`;

const dataFiles = {
  council: dataPath("CapitolAreaCouncil.geojson"),
  counties: dataPath("CapitolAreaCouncil_Counties.geojson"),
  scouting: dataPath("CapitolAreaCouncil_ScoutingDistricts.geojson"),
  schoolDistricts: dataPath("CapitolAreaCouncil_SchoolDistricts.geojson"),
  schoolPoints: dataPath("CapitolAreaCouncil_Schools.geojson"),
  units: dataPath("unit-pins.json"),
  manifest: dataPath("data-manifest.json"),
} as const;

export function useCouncilData() {
  const [data, setData] = useState<CouncilData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all(
      Object.entries(dataFiles).map(async ([key, url]) => {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Could not load ${url}`);
        return [key, await response.json()] as const;
      }),
    )
      .then((entries) => {
        if (!active) return;
        const loaded = Object.fromEntries(entries) as CouncilData;
        setData(loaded);
      })
      .catch((reason: Error) => {
        if (active) setError(reason.message);
      });
    return () => {
      active = false;
    };
  }, []);

  return { data, error };
}
