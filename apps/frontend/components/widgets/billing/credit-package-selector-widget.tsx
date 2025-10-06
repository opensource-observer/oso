"use client";

import React, { useEffect, useState } from "react";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import { useSupabaseState } from "@/components/hooks/supabase";
import { OsoAppClient } from "@/lib/clients/oso-app/oso-app";
import { CREDIT_PACKAGES } from "@/lib/clients/stripe";
import { logger } from "@/lib/logger";

interface CreditPackageSelectorProps {
  className?: string;
  organizationName?: string;
  onPurchaseComplete?: (success: boolean, message?: string) => void;
  showPackageSelection?: boolean;
  defaultPackageId?: string;
}

const CreditPackageSelectorMeta: CodeComponentMeta<CreditPackageSelectorProps> =
  {
    name: "CreditPackageSelector",
    description: "Credit package selector with purchase functionality",
    props: {
      organizationName: {
        type: "string",
        helpText:
          "Organization name to purchase credits for (if not provided, uses user's first organization)",
      },
      onPurchaseComplete: {
        type: "eventHandler",
        argTypes: [
          { name: "success", type: "boolean" },
          { name: "message", type: "string" },
        ],
        helpText: "Callback fired when purchase completes (success/failure)",
      },
      showPackageSelection: {
        type: "boolean",
        defaultValue: true,
        helpText: "Whether to show the package selection interface",
      },
      defaultPackageId: {
        type: "string",
        helpText: "Default package ID to select",
      },
    },
  };

function CreditPackageSelector(props: CreditPackageSelectorProps) {
  const {
    className,
    organizationName,
    onPurchaseComplete,
    showPackageSelection = true,
    defaultPackageId,
  } = props;
  const supabaseState = useSupabaseState();
  const [client, setClient] = useState<OsoAppClient | null>(null);
  const [loading, setLoading] = useState(false);
  const [purchasing, setPurchasing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedPackageId, setSelectedPackageId] = useState<string>(
    defaultPackageId || "",
  );
  const [organization, setOrganization] = useState<{
    id: string;
    org_name: string;
  } | null>(null);

  const session =
    supabaseState._type === "loggedIn" ? supabaseState.session : null;

  useEffect(() => {
    if (supabaseState?.supabaseClient) {
      setClient(new OsoAppClient(supabaseState.supabaseClient));
    }
  }, [supabaseState]);

  useEffect(() => {
    const loadOrganization = async () => {
      if (!client || !session) return;

      try {
        setLoading(true);
        setError(null);

        let targetOrg;
        if (organizationName) {
          targetOrg = await client.getOrganizationByName({
            orgName: organizationName,
          });
        } else {
          const userOrganizations = await client.getMyOrganizations();
          if (userOrganizations.length === 0) {
            setError("You must be part of an organization to purchase credits");
            return;
          }
          targetOrg = userOrganizations[0];
        }

        setOrganization(targetOrg);
      } catch (err) {
        logger.error("Error loading organization:", err);
        setError(
          err instanceof Error ? err.message : "Failed to load organization",
        );
      } finally {
        setLoading(false);
      }
    };

    void loadOrganization();
  }, [client, session, organizationName]);

  useEffect(() => {
    if (defaultPackageId) {
      setSelectedPackageId(defaultPackageId);
    }
  }, [defaultPackageId]);

  const handleBuyCredits = async () => {
    if (!client || !selectedPackageId || !organization) {
      const message =
        "Please select a credit package and ensure you're logged in";
      setError(message);
      onPurchaseComplete?.(false, message);
      return;
    }

    try {
      setPurchasing(true);
      setError(null);

      const result = await client.buyCredits({
        packageId: selectedPackageId,
        orgId: organization.id,
      });

      if (result.url) {
        window.location.href = result.url;
      } else {
        const message = "No checkout URL received";
        setError(message);
        onPurchaseComplete?.(false, message);
      }
    } catch (err) {
      logger.error("Error creating checkout session:", err);
      const message =
        err instanceof Error
          ? err.message
          : "Failed to create checkout session";
      setError(message);
      onPurchaseComplete?.(false, message);
      setPurchasing(false);
    }
  };

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
                Please log in to purchase credits.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className={`${className} mb-8 animate-pulse`}>
        <div className="h-6 w-48 bg-gray-200 rounded mb-4"></div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="border-2 border-gray-200 rounded-xl p-5">
              <div className="h-6 w-32 bg-gray-200 rounded mb-2"></div>
              <div className="h-8 w-20 bg-gray-200 rounded mb-1"></div>
              <div className="h-4 w-24 bg-gray-200 rounded mb-4"></div>
              <div className="h-1 w-full bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
        <div className="h-12 w-full bg-gray-200 rounded"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`${className} mb-8`}>
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
      {showPackageSelection && (
        <>
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
                onClick={() => setSelectedPackageId(pkg.id)}
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
        </>
      )}

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
        onClick={() => void handleBuyCredits()}
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
}

export { CreditPackageSelector, CreditPackageSelectorMeta };
