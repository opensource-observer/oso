import { AnalyticsBrowser } from "@segment/analytics-next";
import { SEGMENT_KEY } from "../config";

export const analytics = AnalyticsBrowser.load({ writeKey: SEGMENT_KEY });
