import { cache } from "react";
import { getArtifactByName, getProjectBySlug } from "@hypercerts-org/indexer";

// Revalidate the data at most every hour
export const revalidate = 3600;
// Cached getters
export const cachedGetArtifactByName = cache(getArtifactByName);
export const cachedGetProjectBySlug = cache(getProjectBySlug);
