import { usePostHog } from "posthog-js/react";
import { useState, useCallback } from "react";
import { TransactionType } from "@/lib/services/credits";
import { useAuth } from "@/lib/hooks/useAuth";
import { logger } from "@/lib/logger";

interface AnalyticsOptions {
  properties?: Record<string, any>;
  transactionType?: TransactionType;
  apiEndpoint?: string;
}

export function useAnalytics() {
  const posthog = usePostHog();
  const { user } = useAuth();
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const trackEvent = useCallback(
    async (eventName: string, options?: AnalyticsOptions): Promise<boolean> => {
      setIsProcessing(true);
      setError(null);

      try {
        posthog.capture(eventName, {
          distinctId: user.role !== "anonymous" ? user.userId : undefined,
          ...options?.properties,
          userRole: user.role,
          apiEndpoint: options?.apiEndpoint,
        });

        setIsProcessing(false);
        return true;
      } catch (err) {
        logger.error("Error tracking event:", err);
        setError("Failed to process event");
        setIsProcessing(false);
        return false;
      }
    },
    [posthog, user],
  );

  return {
    trackEvent,
    isProcessing,
    error,
  };
}
