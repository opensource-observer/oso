import _ from "lodash";
import { NextResponse, type NextRequest } from "next/server";
import {
  eventTimeToLabel,
  csvToArray,
  stringToIntArray,
} from "../../../lib/parsing";
import {
  cachedGetAllEventTypes,
  cachedGetEventSum,
  cachedGetProjectsBySlugs,
  cachedGetProjectsByCollectionSlugs,
} from "../../../lib/graphql/cached-queries";
import { UserInputError } from "../../../lib/types/errors";
import { assert } from "../../../lib/common";

export const runtime = "edge"; // 'nodejs' (default) | 'edge'
export const revalidate = false; // 3600 = 1 hour
const DEFAULT_START_DATE = 0;

type Project = {
  id: number;
  name: string;
  slug: string;
};

/**
 * This will return an array of all artifacts
 * This is currently fetched by Algolia to build the search index
 * @param _request
 * @returns
 */
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const rawCollectionSlugs = searchParams.get("collectionSlugs");
  const rawProjectSlugs = searchParams.get("projectSlugs");
  const rawEventTypeIds = searchParams.get("eventTypeIds");
  const rawEventTypes = searchParams.get("eventTypes");
  const collectionSlugs = csvToArray(rawCollectionSlugs);
  const projectSlugs = csvToArray(rawProjectSlugs);
  const eventTypeIds = stringToIntArray(csvToArray(rawEventTypeIds));
  const eventTypes = csvToArray(rawEventTypes);
  const startDate = eventTimeToLabel(
    searchParams.get("startDate") ?? DEFAULT_START_DATE,
  );
  const endDate = eventTimeToLabel(searchParams.get("endDate") ?? undefined);
  //console.log(projectSlugs, eventTypeIds, startDate, endDate);

  if (collectionSlugs.length < 1 && projectSlugs.length < 1) {
    throw new UserInputError(
      "Missing 1 of required parameters [collectionSlugs, projectSlugs]",
    );
  } else if (eventTypeIds.length < 1 && eventTypes.length < 1) {
    throw new UserInputError(
      "Missing 1 of required parameters [eventTypeIds, eventTypes]",
    );
  }

  // Get Event Types from database
  const { event_type: allEventTypes } = await cachedGetAllEventTypes();
  const eventTypeIdToName = _.fromPairs(
    allEventTypes.map((x) => [x.id, x.name]),
  );
  const eventTypeNameToId = _.fromPairs(
    allEventTypes.map((x) => [x.name, x.id]),
  );

  const getDataByIdAsPair = async (projectId: number, typeId: number) => {
    const response = await cachedGetEventSum({
      projectIds: [projectId],
      typeIds: [typeId],
      startDate,
      endDate,
    });
    return [
      eventTypeIdToName[typeId],
      response.events_monthly_to_project_aggregate?.aggregate?.sum?.amount ??
        "0",
    ];
  };
  const getDataByNameAsPair = async (projectId: number, typeName: string) => {
    if (typeName in eventTypeNameToId) {
      return getDataByIdAsPair(projectId, eventTypeNameToId[typeName]);
    }
    return [typeName, "TODO"];
  };
  const getRowData = async (project: Project) => {
    const dataPairs = await Promise.all([
      ...eventTypes.map((t) => getDataByNameAsPair(project.id, t)),
      ...eventTypeIds.map((t) => getDataByIdAsPair(project.id, t)),
    ]);
    assert(
      eventTypes.length + eventTypeIds.length === dataPairs.length,
      "Missing results",
    );
    return {
      key: project.slug,
      name: project.name,
      ..._.fromPairs(dataPairs),
    };
  };

  // Get projects from database
  const { project: projectsBySlugArray } = await cachedGetProjectsBySlugs({
    slugs: projectSlugs,
  });
  const { project: projectsByCollectionSlugArray } =
    await cachedGetProjectsByCollectionSlugs({
      slugs: collectionSlugs,
    });
  const projectArray = _.uniqBy(
    [...projectsBySlugArray, ...projectsByCollectionSlugArray],
    "slug",
  );

  // Get all aggregate event sums
  const results = await Promise.all(projectArray.map((p) => getRowData(p)));
  const sorted = _.sortBy(results, ["name"]);
  return NextResponse.json(sorted);
}
