"use client";

import dynamic from "next/dynamic";
import { useEffect } from "react";
import posthog from "posthog-js";
import { PostHogProvider as PHProvider } from "posthog-js/react";
import { POSTHOG_HOST, POSTHOG_KEY } from "../../lib/config";

const PostHogPageView = dynamic(() => import("../widgets/posthog-pageview"), {
  ssr: false,
});

function PostHogProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    posthog.init(POSTHOG_KEY, {
      api_host: POSTHOG_HOST,
      capture_pageview: false, // Disable automatic pageview capture, as we capture manually
    });
  }, []);

  return (
    <PHProvider client={posthog}>
      <PostHogPageView />
      {children}
    </PHProvider>
  );
}

export { PostHogProvider };
