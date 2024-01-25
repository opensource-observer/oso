import { notFound } from "next/navigation";
import { NextResponse, type NextRequest } from "next/server";
import { logger } from "../../../lib/logger";
import { cachedGetAllProjects } from "../../../lib/graphql/cached-queries";

export const runtime = "edge"; // 'nodejs' (default) | 'edge'
//export const dynamic = "force-dynamic";
export const revalidate = 0;

/**
 * This will return an array of all artifacts
 * This is currently fetched by Algolia to build the search index
 * @param _request
 * @returns
 */
export async function GET(_request: NextRequest) {
  // Get projects from database
  const { project: projectArray } = await cachedGetAllProjects();
  if (!Array.isArray(projectArray) || projectArray.length < 1) {
    logger.warn(`Cannot find projects`);
    notFound();
  }
  return NextResponse.json(projectArray);
}
