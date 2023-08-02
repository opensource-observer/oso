import { ApiInterface, ApiReturnType, CommonArgs } from "../../../utils/api.js";
import { InvalidInputError } from "../../../utils/error.js";
import { createEventPointersForOrg } from "./createEventPointersForOrg.js";
import { fetchGithubReposForOrg as upsertGithubReposForOrg } from "./upsertGithubReposForOrg.js";

export async function upsertGithubOrg(
  args: UpsertGithubOrgArgs,
): Promise<ApiReturnType> {
  const { orgName } = args;
  if (!orgName) {
    throw new InvalidInputError("Missing required argument: orgName");
  }

  await upsertGithubReposForOrg(orgName);
  await createEventPointersForOrg(orgName);

  return {
    _type: "upToDate",
    cached: true,
  };
}

export type UpsertGithubOrgArgs = Partial<
  CommonArgs & {
    orgName: string;
  }
>;

export const UPSERT_GITHUB_ORG_COMMAND = "upsertGithubOrg";
export const UpsertGithubOrgInterface: ApiInterface<UpsertGithubOrgArgs> = {
  command: UPSERT_GITHUB_ORG_COMMAND,
  func: upsertGithubOrg,
};
