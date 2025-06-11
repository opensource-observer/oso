"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useSupabaseState } from "@/components/hooks/supabase";
import { OsoAppClient } from "@/lib/clients/oso-app/oso-app";
import { CREDIT_PACKAGES } from "@/lib/clients/stripe";
import { logger } from "@/lib/logger";

interface LoadingSpinnerProps {
  message?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = "Loading...",
}) => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <div className="flex flex-col items-center p-8">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="mt-4 text-gray-600 dark:text-gray-300 font-medium">
          {message}
        </p>
      </div>
    </div>
  );
};

const AuthWarning: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto mt-12 px-4">
      <div className="bg-amber-50 border-l-4 border-amber-400 p-4 rounded-r-md">
        <div className="flex">
          <div className="flex-shrink-0">
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
              Please log in to purchase credits.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

interface AlertProps {
  type: "error" | "success";
  message: string;
  onDismiss: () => void;
}

const Alert: React.FC<AlertProps> = ({ type, message, onDismiss }) => {
  const isError = type === "error";
  const bgColor = isError ? "bg-red-50" : "bg-green-50";
  const borderColor = isError ? "border-red-400" : "border-green-400";
  const iconColor = isError ? "text-red-400" : "text-green-400";
  const textColor = isError ? "text-red-800" : "text-green-800";
  const dismissColor = isError ? "text-red-500" : "text-green-500";

  const icon = isError ? (
    <path
      fillRule="evenodd"
      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
      clipRule="evenodd"
    />
  ) : (
    <path
      fillRule="evenodd"
      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
      clipRule="evenodd"
    />
  );

  return (
    <div
      className={`mb-6 ${bgColor} border-l-4 ${borderColor} p-4 rounded-r-md relative`}
    >
      <div className="flex">
        <div className="flex-shrink-0">
          <svg
            className={`h-5 w-5 ${iconColor}`}
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            {icon}
          </svg>
        </div>
        <div className="ml-3">
          <p className={`text-sm ${textColor}`}>{message}</p>
        </div>
      </div>
      <button
        className="absolute top-4 right-4"
        onClick={onDismiss}
        aria-label="Dismiss"
      >
        <svg
          className={`h-4 w-4 ${dismissColor}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>
  );
};

interface CreditBalanceProps {
  balance: number | null;
}

const CreditBalance: React.FC<CreditBalanceProps> = ({ balance }) => {
  return (
    <div className="mb-8 overflow-hidden bg-gradient-to-r from-blue-500 to-indigo-600 rounded-xl shadow-lg">
      <div className="px-8 py-10">
        <div className="flex items-center">
          <svg
            className="h-10 w-10 text-white opacity-75"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div className="ml-5">
            <p className="text-sm font-medium text-blue-100">
              Available Credits
            </p>
            <p className="text-4xl font-bold text-white">
              {balance?.toLocaleString() ?? "0"}
            </p>
          </div>
        </div>
      </div>
      <div className="bg-blue-600/50 px-8 py-4">
        <p className="text-sm text-white">Top up your credits</p>
      </div>
    </div>
  );
};

interface CreditPackageSelectorProps {
  selectedPackageId: string;
  onPackageSelect: (packageId: string) => void;
  onBuyCredits: () => void | Promise<void>;
  purchasing: boolean;
}

const CreditPackageSelector: React.FC<CreditPackageSelectorProps> = ({
  selectedPackageId,
  onPackageSelect,
  onBuyCredits,
  purchasing,
}) => {
  return (
    <div className="mb-8">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
        Select a Credit Package
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {CREDIT_PACKAGES.map((pkg) => (
          <div
            key={pkg.id}
            className={`
              relative overflow-hidden rounded-xl border-2 transition-all duration-200 cursor-pointer
              ${
                selectedPackageId === pkg.id
                  ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-md"
                  : "border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700"
              }
            `}
            onClick={() => onPackageSelect(pkg.id)}
          >
            {selectedPackageId === pkg.id && (
              <div className="absolute top-3 right-3">
                <svg
                  className="h-6 w-6 text-blue-500"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
            )}
            <div className="p-5">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {pkg.name}
              </h3>
              <div className="mt-2 flex items-baseline">
                <span className="text-2xl font-bold text-gray-900 dark:text-white">
                  ${(pkg.price / 100).toFixed(2)}
                </span>
              </div>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
                {pkg.credits.toLocaleString()} credits
              </p>
              <div className="mt-4 h-1 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500"
                  style={{
                    width: `${Math.min(
                      100,
                      Math.max(15, (pkg.credits / 10000) * 100),
                    )}%`,
                  }}
                ></div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <button
        className={`
          mt-6 w-full py-3 px-6 rounded-lg font-medium text-white
          flex items-center justify-center transition-all duration-200
          ${
            !selectedPackageId || purchasing
              ? "bg-blue-400 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-700 shadow-md hover:shadow-lg"
          }
        `}
        onClick={() => void onBuyCredits()}
        disabled={!selectedPackageId || purchasing}
      >
        {purchasing ? (
          <>
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
            Processing...
          </>
        ) : (
          <>
            <svg
              className="h-5 w-5 mr-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"
              />
            </svg>
            Buy Credits
          </>
        )}
      </button>
    </div>
  );
};

interface PurchaseHistoryProps {
  history: Array<{
    id: string;
    status: string;
    package_id: string;
    created_at: string;
    credits_amount: number;
    price_cents: number;
  }>;
}

const PurchaseHistory: React.FC<PurchaseHistoryProps> = ({ history }) => {
  return (
    <div className="mb-8">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
        Purchase History
      </h2>
      {history.length === 0 ? (
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
      ) : (
        <div className="space-y-4">
          {history.map((purchase) => (
            <div
              key={purchase.id}
              className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden"
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
};

const TestPaymentInfo: React.FC = () => {
  return (
    <div className="rounded-xl bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className="px-6 py-5 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          Test Payment Information
        </h3>
      </div>
      <div className="px-6 py-5">
        <p className="text-gray-700 dark:text-gray-300 mb-3">
          Use these test card numbers:
        </p>
        <div className="space-y-2 mb-4">
          <div className="flex items-center">
            <div className="w-6 h-6 flex items-center justify-center bg-green-100 dark:bg-green-900 rounded-full mr-2">
              <svg
                className="h-4 w-4 text-green-600 dark:text-green-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="text-sm font-mono bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
              4242 4242 4242 4242
            </div>
            <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
              Success
            </span>
          </div>
          <div className="flex items-center">
            <div className="w-6 h-6 flex items-center justify-center bg-red-100 dark:bg-red-900 rounded-full mr-2">
              <svg
                className="h-4 w-4 text-red-600 dark:text-red-400"
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
            <div className="text-sm font-mono bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
              4000 0000 0000 0002
            </div>
            <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
              Decline
            </span>
          </div>
        </div>
        <p className="text-gray-700 dark:text-gray-300">
          Use any future expiry date and any 3-digit CVC.
        </p>
      </div>
    </div>
  );
};

function TestCreditsPageContent() {
  const supabaseState = useSupabaseState();
  const searchParams = useSearchParams();
  const [client, setClient] = useState<OsoAppClient | null>(null);
  const [loading, setLoading] = useState(true);
  const [authLoading, setAuthLoading] = useState(true);
  const [purchasing, setPurchasing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [creditBalance, setCreditBalance] = useState<number | null>(null);
  const [selectedPackageId, setSelectedPackageId] = useState<string>("");
  const [purchaseHistory, setPurchaseHistory] = useState<Array<any>>([]);

  useEffect(() => {
    if (supabaseState?.supabaseClient) {
      setClient(new OsoAppClient(supabaseState.supabaseClient));
      setAuthLoading(false);
    }
  }, [supabaseState]);

  useEffect(() => {
    const loadData = async () => {
      if (!client) return;

      try {
        setLoading(true);

        const isRedirectFromPurchase =
          searchParams.get("purchase") === "success";

        if (isRedirectFromPurchase && !supabaseState?.session) {
          await supabaseState?.revalidate?.();
        }

        if (!supabaseState?.session && !isRedirectFromPurchase) {
          setLoading(false);
          return;
        }

        const [balance, history] = await Promise.all([
          client.getMyCredits(),
          client.getMyPurchaseHistory(),
        ]);

        setCreditBalance(balance);
        setPurchaseHistory(history);
      } catch (err) {
        logger.error("Error loading data:", err);
        if (searchParams.get("purchase") !== "success") {
          setError(err instanceof Error ? err.message : "Failed to load data");
        }
      } finally {
        setLoading(false);
      }
    };

    void loadData();
  }, [client, supabaseState?.session, searchParams, supabaseState?.revalidate]);

  useEffect(() => {
    const purchase = searchParams.get("purchase");
    if (purchase === "success") {
      setSuccess("Payment successful! Your credits have been added.");

      if (client && supabaseState?.session) {
        client.getMyCredits().then(setCreditBalance).catch(logger.error);
      }
    } else if (purchase === "cancelled") {
      setError("Payment cancelled. No charges were made.");
    }
  }, [searchParams, client, supabaseState?.session]);

  const handleBuyCredits = async () => {
    if (!client || !selectedPackageId) {
      setError("Please select a credit package");
      return;
    }

    try {
      setPurchasing(true);
      setError(null);
      const result = await client.buyCredits({ packageId: selectedPackageId });

      if (result.url) {
        window.location.href = result.url;
      }
    } catch (err) {
      logger.error("Error creating checkout session:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Failed to create checkout session",
      );
      setPurchasing(false);
    }
  };

  if (loading && (!searchParams.get("purchase") || authLoading)) {
    return <LoadingSpinner message="Loading your credits..." />;
  }

  if (
    !supabaseState?.session &&
    !authLoading &&
    !searchParams.get("purchase")
  ) {
    return <AuthWarning />;
  }

  return (
    <div className="max-w-4xl mx-auto my-12 px-4">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">
        Credit Management
      </h1>

      {error && (
        <Alert type="error" message={error} onDismiss={() => setError(null)} />
      )}

      {success && (
        <Alert
          type="success"
          message={success}
          onDismiss={() => setSuccess(null)}
        />
      )}

      <CreditBalance balance={creditBalance} />

      <CreditPackageSelector
        selectedPackageId={selectedPackageId}
        onPackageSelect={setSelectedPackageId}
        onBuyCredits={handleBuyCredits}
        purchasing={purchasing}
      />

      <PurchaseHistory history={purchaseHistory} />

      <TestPaymentInfo />
    </div>
  );
}

export default function TestCreditsPage() {
  return (
    <Suspense fallback={<LoadingSpinner message="Loading..." />}>
      <TestCreditsPageContent />
    </Suspense>
  );
}
