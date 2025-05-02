import { type NextRequest } from "next/server";
import { PostHog } from "posthog-node";
import { POSTHOG_HOST, POSTHOG_KEY } from "../config";
import { AuthUser, getUser } from "../auth/auth";

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
async function withPostHog(
  fn: (posthog: PostHog, user: AuthUser) => Promise<void>,
  request: NextRequest,
) {
  const user = await getUser(request);
  //console.log(user);
  const posthog = PostHogClient();
  if (user.role !== "anonymous") {
    await fn(posthog, user);
  } else {
    console.warn("PostHog: No user found");
  }
  await posthog.shutdown();
}

export { PostHogClient, withPostHog };
