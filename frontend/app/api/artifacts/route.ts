import { notFound } from "next/navigation";
import { NextResponse, type NextRequest } from "next/server";
import { logger } from "../../../lib/logger";
import { cachedGetAllArtifacts } from "../../../lib/graphql/cached-queries";

export const runtime = "edge"; // 'nodejs' (default) | 'edge'
export const dynamic = "force-dynamic";
export const revalidate = 0;

/**
 * This will return an array of all artifacts
 * This is currently fetched by Algolia to build the search index
 * @param _request
 * @returns
 */
export async function GET(_request: NextRequest) {
  // Get artifacts from database
  const { artifact: artifactArray } = await cachedGetAllArtifacts();
  if (!Array.isArray(artifactArray) || artifactArray.length < 1) {
    logger.warn(`Cannot find artifacts`);
    notFound();
  }
  return NextResponse.json(artifactArray);
}
