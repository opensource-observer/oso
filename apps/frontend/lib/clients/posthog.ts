import { PostHog } from "posthog-node";
import { POSTHOG_HOST, POSTHOG_KEY } from "../config";

/**
 * Use this if you want direct access to the PostHog client
 * - You will need to call posthog.shutdown() when done
 * - You will need to call posthog.capture() manually
 * @returns
 */
function PostHogClient() {
  const posthogClient = new PostHog(POSTHOG_KEY, {
    host: POSTHOG_HOST,
    flushAt: 1,
    flushInterval: 0,
  });
  return posthogClient;
}

/**
 * Use this to simplify PostHog usage,
 * which will automatically identify and teardown
 * @param fn
 * @param request
 */
async function withPostHog(fn: (posthog: PostHog) => Promise<void>) {
  //console.log(user);
  const posthog = PostHogClient();
  await fn(posthog);
  // TODO: this seems to be taking many seconds
  await posthog.shutdown();
}

export { PostHogClient, withPostHog };
