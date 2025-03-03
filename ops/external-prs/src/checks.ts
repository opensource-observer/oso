import { Octokit } from "octokit";

export enum CheckStatus {
  Queued = "queued",
  InProgress = "in_progress",
  Completed = "completed",
  // These are documented at github but don't actually work
  //Waiting = "waiting",
  //Requested = "requested",
  //Pending = "pending",
}

export enum CheckConclusion {
  ActionRequired = "action_required",
  Cancelled = "cancelled",
  Failure = "failure",
  Neutral = "neutral",
  Success = "success",
  Skipped = "skipped",
  Stale = "stale",
  TimedOut = "timed_out",
}

export type CheckOutput = {
  title: string;
  summary: string;
};

export type CheckRequest = {
  name: string;
  head_sha: string;
  status: "queued" | "in_progress" | "completed";
  conclusion?: CheckConclusion;
  output: CheckOutput;
};

export async function setCheckStatus(
  gh: Octokit,
  owner: string,
  repo: string,
  request: CheckRequest,
): Promise<any> {
  if (request.status == CheckStatus.Completed && !request.conclusion) {
    throw new Error("Completed check requires conclusion");
  }
  return await gh.request("POST /repos/{owner}/{repo}/check-runs", {
    owner: owner,
    repo: repo,
    ...request,
    // head_sha: request.head_sha,
    // status: request.status,
    // conclusion: request.conclusion,
    // output: request.output,
  });
}
