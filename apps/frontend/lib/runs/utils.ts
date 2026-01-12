/**
 * Utils for run related operations.
 */
import { Tables } from "@/apps/frontend/lib/types/supabase";

type Run = Partial<Tables<"run">>;

export function getFromRunMetadata<T>(run: Run, key: string): T | undefined {
  if (
    run.metadata &&
    typeof run.metadata === "object" &&
    !Array.isArray(run.metadata)
  ) {
    return run.metadata[key] as T | undefined;
  }
  return undefined;
}
