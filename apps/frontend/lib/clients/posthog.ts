import { PostHog } from "posthog-node";
import { POSTHOG_HOST_DIRECT, POSTHOG_KEY } from "@/lib/config";
import { NextRequest } from "next/server";

let posthogInstance: PostHog | null = null;

/**
 * Use this if you want direct access to the PostHog client
 * - You will need to call posthog.shutdown() when done
 * - You will need to call posthog.capture() manually
 * @returns
 */
function PostHogClient() {
  if (!POSTHOG_KEY) {
    return;
  }
  if (posthogInstance) {
    return posthogInstance;
  }
  posthogInstance = new PostHog(POSTHOG_KEY, {
    // You must send server-side events directly to PostHog.
    // The redirect URL doesn't seem to work for server-side events
    host: POSTHOG_HOST_DIRECT,
    flushAt: 1,
    flushInterval: 0,
  });
  return posthogInstance;
}

/**
 * Use this to simplify PostHog usage for route functions,
 * which will automatically identify and teardown
 * @param fn
 * @param request
 */
function withPostHogTracking(
  fn: (request: NextRequest, ...args: any[]) => Promise<any>,
) {
  //console.log(user);
  return async (request: NextRequest, ...args: any[]) => {
    const posthog = PostHogClient();
    try {
      await fn(request, ...args);
    } catch (error) {
      posthog?.captureException(error);
      throw error;
    } finally {
      // TODO: this seems to be taking many seconds
      await posthog?.shutdown();
    }
  };
}

export { PostHogClient, withPostHogTracking };
