import { User } from "@/lib/types/user";
import { ENABLE_POSTHOG_LOCAL_EVALUATION } from "@/lib/config";
import { PostHogClient } from "@/lib/clients/posthog";
import { logger } from "@/lib/logger";

export const FEATURE_FLAGS = {} as const;

export type FeatureFlagKey = (typeof FEATURE_FLAGS)[keyof typeof FEATURE_FLAGS];

/**
 * Evaluate a PostHog feature flag for a given user.
 * Returns defaultValue (false) if evaluation fails or user is anonymous.
 */
export async function evaluateFeatureFlag(
  flagKey: FeatureFlagKey,
  user: User,
  defaultValue: boolean = false,
): Promise<boolean> {
  const posthog = PostHogClient();

  if (!posthog || user.role === "anonymous") {
    return defaultValue;
  }

  try {
    const personProperties = {
      email: user.email ?? "",
      name: user.name,
      role: user.role,
    };

    const isEnabled = await posthog.isFeatureEnabled(flagKey, user.userId, {
      personProperties,
      sendFeatureFlagEvents: !ENABLE_POSTHOG_LOCAL_EVALUATION,
    });

    return isEnabled ?? defaultValue;
  } catch (error) {
    logger.error(`Error evaluating feature flag ${flagKey}:`, error);
    return defaultValue;
  }
}
