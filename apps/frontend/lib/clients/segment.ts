import { Analytics } from "@segment/analytics-node";
import { AnalyticsBrowser } from "@segment/analytics-next";
import { SEGMENT_KEY } from "../config";

export const serverAnalytics =
  typeof window === "undefined"
    ? new Analytics({ writeKey: SEGMENT_KEY })
    : undefined;
export const clientAnalytics =
  typeof window !== "undefined"
    ? AnalyticsBrowser.load({ writeKey: SEGMENT_KEY })
    : undefined;
