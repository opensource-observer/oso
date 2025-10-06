"use client";

import React, { useEffect, useState } from "react";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import { useSupabaseState } from "@/components/hooks/supabase";
import { OsoAppClient } from "@/lib/clients/oso-app/oso-app";
import { logger } from "@/lib/logger";

interface PurchaseHistoryProps {
  className?: string;
  limit?: number;
  showEmptyState?: boolean;
  refreshTrigger?: number;
}

interface PurchaseRecord {
  id: string;
  status: string;
  package_id: string;
  created_at: string;
  credits_amount: number;
  price_cents: number;
}

const PurchaseHistoryMeta: CodeComponentMeta<PurchaseHistoryProps> = {
  name: "PurchaseHistory",
  description: "Display user's credit purchase history",
  props: {
    limit: {
      type: "number",
      defaultValue: 10,
      helpText: "Maximum number of purchase records to display",
    },
    showEmptyState: {
      type: "boolean",
      defaultValue: true,
      helpText: "Whether to show empty state when no purchases exist",
    },
    refreshTrigger: {
      type: "number",
      helpText:
        "Change this value to trigger a refresh of the purchase history",
    },
  },
};

function PurchaseHistory(props: PurchaseHistoryProps) {
  const {
    className,
    limit = 10,
    showEmptyState = true,
    refreshTrigger,
  } = props;
  const supabaseState = useSupabaseState();
  const [client, setClient] = useState<OsoAppClient | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [purchaseHistory, setPurchaseHistory] = useState<PurchaseRecord[]>([]);

  const session =
    supabaseState._type === "loggedIn" ? supabaseState.session : null;

  useEffect(() => {
    if (supabaseState?.supabaseClient) {
      setClient(new OsoAppClient(supabaseState.supabaseClient));
    }
  }, [supabaseState]);

  useEffect(() => {
    const loadPurchaseHistory = async () => {
      if (!client || !session) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const history = await client.getMyPurchaseHistory();
        const limitedHistory = limit > 0 ? history.slice(0, limit) : history;
        setPurchaseHistory(limitedHistory);
      } catch (err) {
        logger.error("Error loading purchase history:", err);
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load purchase history",
        );
      } finally {
        setLoading(false);
      }
    };

    void loadPurchaseHistory();
  }, [client, session, limit, refreshTrigger]);

  if (!session) {
    return (
      <div className={`${className} mb-8`}>
        <div className="bg-amber-50 border-l-4 border-amber-400 p-4 rounded-r-md">
          <div className="flex">
            <div className="shrink-0">
              <svg
                className="h-5 w-5 text-amber-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-amber-800">
                Please log in to view purchase history.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className={`${className} mb-8`}>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Purchase History
        </h2>
        <div className="space-y-4 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="bg-white dark:bg-gray-800 rounded-xl shadow-xs border border-gray-200 dark:border-gray-700 overflow-hidden"
            >
              <div className="p-4 sm:p-5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between">
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-gray-200 rounded-full mr-3"></div>
                    <div className="space-y-2">
                      <div className="h-4 w-24 bg-gray-200 rounded"></div>
                      <div className="h-3 w-32 bg-gray-200 rounded"></div>
                    </div>
                  </div>
                  <div className="mt-3 sm:mt-0 flex items-center space-x-6">
                    <div className="space-y-2">
                      <div className="h-3 w-12 bg-gray-200 rounded"></div>
                      <div className="h-4 w-16 bg-gray-200 rounded"></div>
                    </div>
                    <div className="space-y-2">
                      <div className="h-3 w-8 bg-gray-200 rounded"></div>
                      <div className="h-4 w-12 bg-gray-200 rounded"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`${className} mb-8`}>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Purchase History
        </h2>
        <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded-r-md">
          <div className="flex">
            <div className="shrink-0">
              <svg
                className="h-5 w-5 text-red-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`${className} mb-8`}>
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
        Purchase History
      </h2>
      {purchaseHistory.length === 0 ? (
        showEmptyState && (
          <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-6 text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
              />
            </svg>
            <p className="mt-4 text-gray-500 dark:text-gray-400">
              No purchase history yet
            </p>
          </div>
        )
      ) : (
        <div className="space-y-4">
          {purchaseHistory.map((purchase) => (
            <div
              key={purchase.id}
              className="bg-white dark:bg-gray-800 rounded-xl shadow-xs border border-gray-200 dark:border-gray-700 overflow-hidden"
            >
              <div className="p-4 sm:p-5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between">
                  <div>
                    <div className="flex items-center">
                      <span
                        className={`
                        inline-flex items-center justify-center w-8 h-8 rounded-full mr-3
                        ${
                          purchase.status === "completed"
                            ? "bg-green-100 text-green-600"
                            : "bg-yellow-100 text-yellow-600"
                        }
                      `}
                      >
                        {purchase.status === "completed" ? (
                          <svg
                            className="h-5 w-5"
                            viewBox="0 0 20 20"
                            fill="currentColor"
                          >
                            <path
                              fillRule="evenodd"
                              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                              clipRule="evenodd"
                            />
                          </svg>
                        ) : (
                          <svg
                            className="h-5 w-5"
                            viewBox="0 0 20 20"
                            fill="currentColor"
                          >
                            <path
                              fillRule="evenodd"
                              d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"
                              clipRule="evenodd"
                            />
                          </svg>
                        )}
                      </span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {purchase.package_id}
                      </span>
                    </div>
                    <div className="mt-2 ml-11 text-sm text-gray-500 dark:text-gray-400">
                      {new Date(purchase.created_at).toLocaleString()}
                    </div>
                  </div>
                  <div className="ml-11 sm:ml-0 mt-3 sm:mt-0 flex items-center">
                    <div className="mr-6">
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        Credits
                      </p>
                      <p className="text-lg font-medium text-gray-900 dark:text-white">
                        {purchase.credits_amount.toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        Price
                      </p>
                      <p className="text-lg font-medium text-gray-900 dark:text-white">
                        ${(purchase.price_cents / 100).toFixed(2)}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export { PurchaseHistory, PurchaseHistoryMeta };
