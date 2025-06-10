import * as React from "react";
import { PlasmicCanvasHost } from "@plasmicapp/loader-nextjs";
import "../../plasmic-init-client";

// Use revalidate if you want incremental static regeneration
export const dynamic = "force-static";
export const revalidate = false; // 3600 = 1 hour

export default function PlasmicHost() {
  return <PlasmicCanvasHost />;
}
