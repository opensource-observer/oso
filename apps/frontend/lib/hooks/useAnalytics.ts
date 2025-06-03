import { usePostHog } from "posthog-js/react";
import { useState, useCallback } from "react";
import { CreditsService, TransactionType } from "../services/credits";
import { useAuth } from "./useAuth";
import { logger } from "../logger";

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
        if (
          options?.transactionType &&
          [
            TransactionType.SQL_QUERY,
            TransactionType.GRAPHQL_QUERY,
            TransactionType.CHAT_QUERY,
          ].includes(options.transactionType)
        ) {
          if (user.role !== "anonymous") {
            const success = await CreditsService.checkAndDeductCredits(
              user,
              options.transactionType,
              options.apiEndpoint,
              options.properties,
            );

            if (!success) {
              setError("Insufficient credits");
              setIsProcessing(false);
              return false;
            }
          } else {
            setError("Authentication required");
            setIsProcessing(false);
            return false;
          }
        }

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
