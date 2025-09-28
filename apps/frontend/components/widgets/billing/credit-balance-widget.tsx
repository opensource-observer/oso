"use client";

import React, { useEffect, useState } from "react";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import { useSupabaseState } from "@/components/hooks/supabase";
import { OsoAppClient } from "@/lib/clients/oso-app/oso-app";
import { logger } from "@/lib/logger";

interface CreditBalanceProps {
  className?: string;
  organizationName?: string;
  showOrganizationName?: boolean;
  refreshTrigger?: number;
}

const CreditBalanceMeta: CodeComponentMeta<CreditBalanceProps> = {
  name: "CreditBalance",
  description: "Display organization credit balance with real-time updates",
  props: {
    organizationName: {
      type: "string",
      helpText:
        "Organization name to display credits for (if not provided, uses user's first organization)",
    },
    showOrganizationName: {
      type: "boolean",
      defaultValue: true,
      helpText: "Whether to show the organization name in the display",
    },
    refreshTrigger: {
      type: "number",
      helpText: "Change this value to trigger a refresh of the credit balance",
    },
  },
};

function CreditBalance(props: CreditBalanceProps) {
  const {
    className,
    organizationName,
    showOrganizationName = true,
    refreshTrigger,
  } = props;
  const supabaseState = useSupabaseState();
  const [client, setClient] = useState<OsoAppClient | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creditBalance, setCreditBalance] = useState<number | null>(null);
  const [resolvedOrgName, setResolvedOrgName] = useState<string | null>(null);

  useEffect(() => {
    if (supabaseState?.supabaseClient) {
      setClient(new OsoAppClient(supabaseState.supabaseClient));
    }
  }, [supabaseState]);

  useEffect(() => {
    const loadCreditBalance = async () => {
      if (!client) return;

      try {
        setLoading(true);
        setError(null);

        let targetOrgName = organizationName;

        if (!targetOrgName) {
          const userOrganizations = await client.getMyOrganizations();
          if (userOrganizations.length === 0) {
            setError("You must be part of an organization to view credits");
            return;
          }
          targetOrgName = userOrganizations[0].org_name;
        }

        setResolvedOrgName(targetOrgName);
        const balance = await client.getOrganizationCredits({
          orgName: targetOrgName,
        });
        setCreditBalance(balance);
      } catch (err) {
        logger.error("Error loading credit balance:", err);
        setError(
          err instanceof Error ? err.message : "Failed to load credit balance",
        );
      } finally {
        setLoading(false);
      }
    };

    void loadCreditBalance();
  }, [client, organizationName, refreshTrigger]);

  if (loading) {
    return (
      <div
        className={`${className} mb-8 overflow-hidden bg-gradient-to-r from-blue-500 to-indigo-600 rounded-xl shadow-lg animate-pulse`}
      >
        <div className="px-8 py-10">
          <div className="flex items-center">
            <div className="h-10 w-10 bg-white/20 rounded-full"></div>
            <div className="ml-5 space-y-2">
              <div className="h-4 w-32 bg-white/20 rounded"></div>
              <div className="h-8 w-24 bg-white/20 rounded"></div>
            </div>
          </div>
        </div>
        <div className="bg-blue-600/50 px-8 py-4">
          <div className="h-4 w-28 bg-white/20 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className={`${className} mb-8 overflow-hidden bg-gradient-to-r from-red-500 to-red-600 rounded-xl shadow-lg`}
      >
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
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
            <div className="ml-5">
              <p className="text-sm font-medium text-red-100">
                Error Loading Credits
              </p>
              <p className="text-2xl font-bold text-white">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`${className} mb-8 overflow-hidden bg-gradient-to-r from-blue-500 to-indigo-600 rounded-xl shadow-lg`}
    >
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
              Available Credits{" "}
              {showOrganizationName &&
                resolvedOrgName &&
                `for ${resolvedOrgName}`}
            </p>
            <p className="text-4xl font-bold text-white">
              {creditBalance?.toLocaleString() ?? "0"}
            </p>
          </div>
        </div>
      </div>
      <div className="bg-blue-600/50 px-8 py-4">
        <p className="text-sm text-white">Top up your credits below</p>
      </div>
    </div>
  );
}

export { CreditBalance, CreditBalanceMeta };
