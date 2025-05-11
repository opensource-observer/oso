import { PostHog } from "posthog-node";
import { POSTHOG_HOST_DIRECT, POSTHOG_KEY } from "../config";

/**
 * Use this if you want direct access to the PostHog client
 * - You will need to call posthog.shutdown() when done
 * - You will need to call posthog.capture() manually
 * @returns
 */
function PostHogClient() {
  const posthogClient = new PostHog(POSTHOG_KEY, {
    // You must send server-side events directly to PostHog.
    // The redirect URL doesn't seem to work for server-side events
    host: POSTHOG_HOST_DIRECT,
    flushAt: 1,
    flushInterval: 0,
    fetch: (...args) => fetch(...args),
  });
  return posthogClient;
}

/**
 * Creates a disposable PostHog instance
 * - Automatically calls posthog.shutdown() when done
 * @returns
 */
function createPostHog() {
  const posthog = PostHogClient();

  return {
    client: posthog,
    [Symbol.asyncDispose]: async () => {
      // TODO: this seems to be taking many seconds
      await posthog.shutdown();
    },
  };
}

export { PostHogClient, createPostHog };
