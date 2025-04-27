import { PostHog } from "posthog-node";
import { POSTHOG_HOST, POSTHOG_KEY } from "../config";

function PostHogClient() {
  const posthogClient = new PostHog(POSTHOG_KEY, {
    host: POSTHOG_HOST,
    flushAt: 1,
    flushInterval: 0,
  });
  return posthogClient;
}

export { PostHogClient };
