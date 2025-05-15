import { User } from "../types/user";
import { PostHogClient } from "../clients/posthog";
import { spawn } from "@opensource-observer/utils";
import { usePostHog } from "posthog-js/react";
import { useAuth } from "../hooks/useAuth";
import { useCallback } from "react";

export async function trackServerEvent(
  user: User,
  eventName: string,
  properties: Record<string, any> = {},
) {
  if (user.role === "anonymous") {
    return;
  }

  return spawn(
    (async () => {
      const posthog = PostHogClient();
      try {
        posthog.capture({
          distinctId: user.userId,
          event: eventName,
          properties: {
            ...properties,
            apiKeyName: user.keyName,
            host: user.host,
            userRole: user.role,
          },
        });
      } finally {
        await posthog.shutdown();
      }
    })(),
  );
}

export function useTrack() {
  const { user, isAuthenticated } = useAuth();
  const posthog = usePostHog();

  const trackEvent = useCallback(
    (eventName: string, properties: Record<string, any> = {}) => {
      if (isAuthenticated && posthog && user.role !== "anonymous") {
        posthog.capture(eventName, {
          distinctId: user.userId,
          ...properties,
          apiKeyName: user.keyName,
          host: user.host,
          userRole: user.role,
        });
        return true;
      }
      return false;
    },
    [posthog, user, isAuthenticated],
  );

  return { trackEvent };
}
