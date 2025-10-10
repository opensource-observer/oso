"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import { useSupabaseState } from "@/components/hooks/supabase";
import { OsoAppClient } from "@/lib/clients/oso-app/oso-app";
import { CreditBalance } from "@/components/widgets/billing/credit-balance-widget";
import { EnterpriseContact } from "@/components/widgets/billing/enterprise-contact-widget";
import { TallyPopup } from "@/components/widgets/tally";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { logger } from "@/lib/logger";

interface BillingProps {
  className?: string;
  organizationName?: string;
  showCreditBalance?: boolean;
  handleUrlParams?: boolean;
  title?: string;
  previewPlanName?: "FREE" | "ENTERPRISE";
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
    "Billing management interface that adapts based on pricing plan (FREE shows upgrade form, ENTERPRISE shows support contacts)",
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
    handleUrlParams: {
      type: "boolean",
      defaultValue: false,
      helpText:
        "Whether to handle URL parameters for payment success/cancel states (legacy)",
    },
    title: {
      type: "string",
      defaultValue: "Billing",
      helpText: "Title to display at the top of the widget",
    },
    previewPlanName: {
      type: "choice",
      options: ["FREE", "ENTERPRISE"],
      helpText: "Preview mode: set the plan type for testing in Plasmic",
      editOnly: true,
    },
  },
};

function BillingContent(props: BillingProps) {
  const {
    className,
    organizationName,
    showCreditBalance = true,
    handleUrlParams = false,
    title = "Billing",
    previewPlanName,
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
    pricing_plan?: {
      plan_name: string;
    };
  } | null>(null);
  const [planName, setPlanName] = useState<string | null>(null);

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
          targetOrg = await client.getOrganizationById({
            orgId: userOrganizations[0].id,
          });
        }

        setOrganization(targetOrg);

        const actualPlanName =
          previewPlanName || targetOrg.pricing_plan?.plan_name || "FREE";
        setPlanName(actualPlanName);
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
    previewPlanName,
  ]);

  useEffect(() => {
    if (!handleUrlParams) return;

    const purchase = searchParams.get("purchase");
    if (purchase === "success") {
      setSuccess("Payment successful! Your credits have been added.");
    } else if (purchase === "cancelled") {
      setError("Payment cancelled. No charges were made.");
    }
  }, [searchParams, handleUrlParams]);

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

  const isFree = planName === "FREE";
  const isEnterprise = planName === "ENTERPRISE";

  return (
    <div className={`${className} max-w-4xl mx-auto my-12 px-4`}>
      <h1 className="text-3xl font-bold text-[#253494] mb-6">{title}</h1>

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
        <CreditBalance organizationName={organization.org_name} />
      )}

      {isFree && (
        <Card className="border-[#41B6C4]/30 bg-gradient-to-br from-white to-[#99D8C9]/5">
          <CardHeader>
            <CardTitle className="text-[#253494]">
              Upgrade to Enterprise
            </CardTitle>
            <CardDescription className="text-[#253494]/70">
              Need more credits or advanced features? Get in touch with our team
              to learn about Enterprise plans with higher credit limits,
              priority support, and more.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <TallyPopup formId="wbb196" layout="modal" width="600">
              <Button
                size="lg"
                className="w-full sm:w-auto bg-[#253494] hover:bg-[#2C7FB8] text-white"
              >
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
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
                Request Enterprise Upgrade
              </Button>
            </TallyPopup>
          </CardContent>
        </Card>
      )}

      {isEnterprise && organization && (
        <EnterpriseContact
          organizationName={organization.org_name}
          previewMode={!!previewPlanName}
        />
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
