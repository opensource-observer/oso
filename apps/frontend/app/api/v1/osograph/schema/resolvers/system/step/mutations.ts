import { getSystemClient } from "@/app/api/v1/osograph/utils/access-control";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  ResourceErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import {
  FinishStepSchema,
  StartStepSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import {
  MutationFinishStepArgs,
  MutationStartStepArgs,
} from "@/lib/graphql/generated/graphql";

type StepStatus = "running" | "success" | "failed" | "canceled";
const StepStatusMap: Record<string, StepStatus> = {
  RUNNING: "running",
  SUCCESS: "success",
  FAILED: "failed",
  CANCELED: "canceled",
};

export const stepMutationResolvers: GraphQLResolverModule<GraphQLContext> = {
  Mutation: {
    startStep: async (
      _: unknown,
      args: MutationStartStepArgs,
      context: GraphQLContext,
    ) => {
      const client = getSystemClient(context);

      const { runId, name, displayName } = validateInput(
        StartStepSchema,
        args.input,
      );

      // Get the run to ensure it exists
      const { data: runData, error: runError } = await client
        .from("run")
        .select("org_id")
        .eq("id", runId)
        .single();
      if (runError || !runData) {
        throw ResourceErrors.notFound(`Run ${runId} not found`);
      }

      // We start a new step for the given run
      const { data: stepData, error: stepError } = await client
        .from("step")
        .insert({
          run_id: runId,
          name,
          org_id: runData.org_id,
          display_name: displayName,
          status: "running",
          started_at: new Date().toISOString(),
        })
        .select()
        .single();
      if (stepError || !stepData) {
        throw ServerErrors.internal(
          `Failed to start step ${name} for run ${runId}`,
        );
      }

      return { message: "Started step", success: true, step: stepData };
    },

    finishStep: async (
      _: unknown,
      args: MutationFinishStepArgs,
      context: GraphQLContext,
    ) => {
      const client = getSystemClient(context);

      const { stepId, logsUrl, status } = validateInput(
        FinishStepSchema,
        args.input,
      );

      const { data: stepData, error: stepError } = await client
        .from("step")
        .select("*")
        .eq("id", stepId)
        .single();
      if (stepError || !stepData) {
        throw ResourceErrors.notFound(`Step ${stepId} not found`);
      }

      // Update the status and logsUrl of the step based on the input
      const { data: updatedStep, error: updateError } = await client
        .from("step")
        .update({
          status: StepStatusMap[status] || "failed",
          logs_url: logsUrl,
          completed_at: new Date().toISOString(),
        })
        .eq("id", stepId)
        .select()
        .single();
      if (updateError || !updatedStep) {
        throw ServerErrors.internal(
          `Failed to update step ${stepId} status to ${status}`,
        );
      }

      return {
        message: "Committed step completion",
        success: true,
        step: updatedStep,
      };
    },
  },
};
