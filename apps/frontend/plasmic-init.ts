import { initPlasmicLoader } from "@plasmicapp/loader-nextjs/react-server-conditional";
import _ from "lodash";
import { assert, ensure } from "@opensource-observer/utils";
import { PLASMIC_PROJECT_ID, PLASMIC_PROJECT_API_TOKEN } from "./lib/config";

const DELIMITER = ",";
const ids = _.compact(PLASMIC_PROJECT_ID.split(DELIMITER));
const tokens = _.compact(PLASMIC_PROJECT_API_TOKEN.split(DELIMITER));
assert(
  ids.length === tokens.length,
  `Plasmic Project ID count (${ids.length}) and API token count (${tokens.length}) mismatch`,
);

export const PLASMIC = initPlasmicLoader({
  projects: _.zip(ids, tokens).map(([id, token]) => {
    const project: { id: string; token: string; version?: string } = {
      id: ensure(id, "Plasmic Project ID is required"),
      token: ensure(token, "Plasmic Project API token is required"),
    };
    if (process.env.PLASMIC_BRANCH !== "") {
      project.version = process.env.PLASMIC_BRANCH;
    }
    return project;
  }),
  // Fetches the latest revisions, whether or not they were unpublished!
  // Disable for production to ensure you render only published changes.
  preview: false,
});
