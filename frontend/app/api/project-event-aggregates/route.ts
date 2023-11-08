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
} from "../../../lib/graphql/cached-queries";
import { UserInputError } from "../../../lib/types/errors";
import { assert } from "../../../lib/common";

export const revalidate = 3600;
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
  const rawProjectSlugs = searchParams.get("projectSlugs");
  const rawEventTypeIds = searchParams.get("eventTypeIds");
  const rawEventTypes = searchParams.get("eventTypes");
  const projectSlugs = csvToArray(rawProjectSlugs);
  const eventTypeIds = stringToIntArray(csvToArray(rawEventTypeIds));
  const eventTypes = csvToArray(rawEventTypes);
  const startDate = eventTimeToLabel(
    searchParams.get("startDate") ?? DEFAULT_START_DATE,
  );
  const endDate = eventTimeToLabel(searchParams.get("endDate") ?? undefined);
  //console.log(projectSlugs, eventTypeIds, startDate, endDate);

  if (projectSlugs.length < 1) {
    throw new UserInputError("Missing required parameter projectSlugs");
  } else if (eventTypeIds.length < 1 && eventTypes.length < 1) {
    throw new UserInputError(
      "Missing 1 of required parameter [eventTypeIds, eventTypes]",
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
      response.events_daily_to_project_aggregate?.aggregate?.sum?.amount ?? "?",
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
  const { project: projectArray } = await cachedGetProjectsBySlugs({
    slugs: projectSlugs,
  });

  // Get all aggregate event sums
  const results = await Promise.all(projectArray.map((p) => getRowData(p)));
  const sorted = _.sortBy(results, ["name"]);
  return NextResponse.json(sorted);
}
