import type { Metadata } from "next";
import { MapExplorer } from "./MapExplorer";

export const metadata: Metadata = {
  title: "Council School Atlas",
  description:
    "Explore schools, school districts, and council geography across Central Texas.",
};

export default function Home() {
  return <MapExplorer />;
}
