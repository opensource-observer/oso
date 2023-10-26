import _ from "lodash";
import { NextResponse, type NextRequest } from "next/server";
import {
  eventTimeToLabel,
  csvToArray,
  stringToIntArray,
} from "../../../lib/parsing";
import {
  cachedGetEventTypesByIds,
  cachedGetEventSum,
  cachedGetProjectsBySlugs,
} from "../../../lib/graphql/cached-queries";
import { UserInputError, MissingDataError } from "../../../lib/types/errors";

// TODO: Update to cache
export const dynamic = "force-dynamic";
export const revalidate = 0;

const DEFAULT_START_DATE = 0;

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
  const projectSlugs = csvToArray(rawProjectSlugs);
  const eventTypeIds = stringToIntArray(csvToArray(rawEventTypeIds));
  const startDate = eventTimeToLabel(
    searchParams.get("startDate") ?? DEFAULT_START_DATE,
  );
  const endDate = eventTimeToLabel(searchParams.get("endDate") ?? undefined);
  //console.log(projectSlugs, eventTypeIds, startDate, endDate);

  if (projectSlugs.length < 1) {
    throw new UserInputError("Missing required parameter projectSlugs");
  } else if (eventTypeIds.length < 1) {
    throw new UserInputError("Missing required parameter eventTypeIds");
  }

  // Get Event Types from database
  const { event_type: eventTypeArray } = await cachedGetEventTypesByIds({
    typeIds: eventTypeIds,
  });
  const eventTypeMap = _.fromPairs(eventTypeArray.map((x) => [x.id, x.name]));

  // Get projects from database
  const { project: projectArray } = await cachedGetProjectsBySlugs({
    slugs: projectSlugs,
  });
  // Get all aggregate event sums
  const queries = Promise.all(
    projectArray.map((project) =>
      Promise.all(
        eventTypeIds.map((typeId) =>
          cachedGetEventSum({
            projectIds: [project.id],
            typeIds: [typeId],
            startDate,
            endDate,
          }),
        ),
      ),
    ),
  );
  const results = await queries;

  if (projectArray.length !== results.length) {
    throw new MissingDataError(
      `Projects array length (${projectArray.length}) does not match results length (${results.length})`,
    );
  }

  const data = _.zip(projectArray, results).map(([p, r]) => ({
    name: p?.name,
    ..._.fromPairs(
      _.zip(
        eventTypeIds.map((id) => eventTypeMap[id]),
        r?.map(
          (x) =>
            x.events_daily_to_project_aggregate.aggregate?.sum?.amount ?? 0,
        ),
      ),
    ),
  }));

  return NextResponse.json(data);
}
