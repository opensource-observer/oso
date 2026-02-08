import { User } from "@/lib/types/user";
import {
  FEATURE_FLAG_NEW_RESOLVERS,
  ENABLE_POSTHOG_LOCAL_EVALUATION,
} from "@/lib/config";
import { PostHogClient } from "@/lib/clients/posthog";
import { logger } from "@/lib/logger";

export const FEATURE_FLAGS = {
  NEW_GRAPHQL_RESOLVERS: FEATURE_FLAG_NEW_RESOLVERS,
} as const;

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

/**
 * Batch evaluate multiple feature flags for better performance.
 */
export async function evaluateFeatureFlags(
  flagKeys: FeatureFlagKey[],
  user: User,
): Promise<Map<FeatureFlagKey, boolean>> {
  const results = new Map<FeatureFlagKey, boolean>();

  await Promise.all(
    flagKeys.map(async (flagKey) => {
      const value = await evaluateFeatureFlag(flagKey, user);
      results.set(flagKey, value);
    }),
  );

  return results;
}

/**
 * Helper function specifically for the new resolvers feature flag.
 * Returns true if the user should receive the new GraphQL resolvers.
 */
export async function shouldUseNewResolvers(user: User): Promise<boolean> {
  return evaluateFeatureFlag(FEATURE_FLAGS.NEW_GRAPHQL_RESOLVERS, user, false);
}
