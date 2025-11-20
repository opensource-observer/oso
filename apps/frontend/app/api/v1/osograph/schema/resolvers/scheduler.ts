import { ModelRunRow } from "@/lib/types/schema-types";
import { RunStatus } from "@/lib/graphql/generated/graphql";

function mapRunStatus(status: ModelRunRow["status"]): RunStatus {
  switch (status) {
    case "running":
      return RunStatus.Running;
    case "completed":
      return RunStatus.Success;
    case "failed":
      return RunStatus.Failed;
    case "canceled":
      return RunStatus.Canceled;
    default:
      throw Error(`Unknown run status: ${status}`);
  }
}

export const schedulerResolvers = {
  Run: {
    status: (parent: ModelRunRow) => mapRunStatus(parent.status),
    startedAt: (parent: ModelRunRow) => parent.started_at,
    finishedAt: (parent: ModelRunRow) => parent.completed_at,
  },
};
