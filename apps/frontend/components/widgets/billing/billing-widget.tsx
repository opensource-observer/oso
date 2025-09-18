"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import { useSupabaseState } from "@/components/hooks/supabase";
import { OsoAppClient } from "@/lib/clients/oso-app/oso-app";
import { CreditBalance } from "@/apps/frontend/components/widgets/billing/credit-balance-widget";
import { CreditPackageSelector } from "@/apps/frontend/components/widgets/billing/credit-package-selector-widget";
import { PurchaseHistory } from "@/apps/frontend/components/widgets/billing/purchase-history-widget";
import { logger } from "@/lib/logger";

interface BillingProps {
  className?: string;
  organizationName?: string;
  showCreditBalance?: boolean;
  showPackageSelector?: boolean;
  showPurchaseHistory?: boolean;
  handleUrlParams?: boolean;
  title?: string;
}

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
        <div className="shrink-0">
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

const LoadingSpinner: React.FC<{ message?: string }> = ({
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

const BillingMeta: CodeComponentMeta<BillingProps> = {
  name: "Billing",
  description:
    "Complete billing management interface with credit balance, package selection, and purchase history",
  props: {
    organizationName: {
      type: "string",
      helpText:
        "Organization name to manage billing for (if not provided, uses user's first organization)",
    },
    showCreditBalance: {
      type: "boolean",
      defaultValue: true,
      helpText: "Whether to show the credit balance section",
    },
    showPackageSelector: {
      type: "boolean",
      defaultValue: true,
      helpText: "Whether to show the credit package selector",
    },
    showPurchaseHistory: {
      type: "boolean",
      defaultValue: true,
      helpText: "Whether to show the purchase history section",
    },
    handleUrlParams: {
      type: "boolean",
      defaultValue: true,
      helpText:
        "Whether to handle URL parameters for payment success/cancel states",
    },
    title: {
      type: "string",
      defaultValue: "Credit Management",
      helpText: "Title to display at the top of the widget",
    },
  },
};

function BillingContent(props: BillingProps) {
  const {
    className,
    organizationName,
    showCreditBalance = true,
    showPackageSelector = true,
    showPurchaseHistory = true,
    handleUrlParams = true,
    title = "Credit Management",
  } = props;

  const supabaseState = useSupabaseState();
  const searchParams = useSearchParams();
  const [client, setClient] = useState<OsoAppClient | null>(null);
  const [loading, setLoading] = useState(true);
  const [authLoading, setAuthLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [organization, setOrganization] = useState<{
    id: string;
    org_name: string;
  } | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const session =
    supabaseState._type === "loggedIn" ? supabaseState.session : null;

  useEffect(() => {
    if (supabaseState?.supabaseClient) {
      setClient(new OsoAppClient(supabaseState.supabaseClient));
      setAuthLoading(false);
    }
  }, [supabaseState]);

  useEffect(() => {
    const loadOrganization = async () => {
      if (!client) return;

      try {
        setLoading(true);

        const isRedirectFromPurchase =
          handleUrlParams && searchParams.get("purchase") === "success";

        if (
          isRedirectFromPurchase &&
          !session &&
          supabaseState._type !== "loading"
        ) {
          await supabaseState.revalidate();
        }

        if (!session && !isRedirectFromPurchase) {
          setLoading(false);
          return;
        }

        let targetOrg;
        if (organizationName) {
          targetOrg = await client.getOrganizationByName({
            orgName: organizationName,
          });
        } else {
          const userOrganizations = await client.getMyOrganizations();
          if (userOrganizations.length === 0) {
            setError("You must be part of an organization to manage credits");
            setLoading(false);
            return;
          }
          targetOrg = userOrganizations[0];
        }

        setOrganization(targetOrg);
      } catch (err) {
        logger.error("Error loading organization:", err);
        if (!handleUrlParams || searchParams.get("purchase") !== "success") {
          setError(
            err instanceof Error ? err.message : "Failed to load organization",
          );
        }
      } finally {
        setLoading(false);
      }
    };

    void loadOrganization();
  }, [
    client,
    session,
    searchParams,
    supabaseState,
    organizationName,
    handleUrlParams,
  ]);

  useEffect(() => {
    if (!handleUrlParams) return;

    const purchase = searchParams.get("purchase");
    if (purchase === "success") {
      setSuccess("Payment successful! Your credits have been added.");
      setRefreshTrigger((prev) => prev + 1);
    } else if (purchase === "cancelled") {
      setError("Payment cancelled. No charges were made.");
    }
  }, [searchParams, handleUrlParams]);

  const handlePurchaseComplete = (success: boolean, message?: string) => {
    if (success) {
      setSuccess(message || "Purchase completed successfully!");
      setRefreshTrigger((prev) => prev + 1);
    } else {
      setError(message || "Purchase failed");
    }
  };

  if (
    loading &&
    (!handleUrlParams || !searchParams.get("purchase") || authLoading)
  ) {
    return <LoadingSpinner message="Loading your billing information..." />;
  }

  if (
    !session &&
    !authLoading &&
    (!handleUrlParams || !searchParams.get("purchase"))
  ) {
    return (
      <div className={`${className} max-w-4xl mx-auto mt-12 px-4`}>
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
                Please log in to manage your billing.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`${className} max-w-4xl mx-auto my-12 px-4`}>
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">
        {title}
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

      {showCreditBalance && organization && (
        <CreditBalance
          organizationName={organization.org_name}
          refreshTrigger={refreshTrigger}
        />
      )}

      {showPackageSelector && organization && (
        <CreditPackageSelector
          organizationName={organization.org_name}
          onPurchaseComplete={handlePurchaseComplete}
        />
      )}

      {showPurchaseHistory && (
        <PurchaseHistory refreshTrigger={refreshTrigger} />
      )}
    </div>
  );
}

function Billing(props: BillingProps) {
  return (
    <Suspense fallback={<LoadingSpinner message="Loading billing..." />}>
      <BillingContent {...props} />
    </Suspense>
  );
}

export { Billing, BillingMeta };
