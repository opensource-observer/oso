"use client";

import React, { useEffect, useState } from "react";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import { useSupabaseState } from "@/components/hooks/supabase";
import { OsoAppClient } from "@/lib/clients/oso-app/oso-app";
import { logger } from "@/lib/logger";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";

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
      <Card className={`${className} mb-6`}>
        <CardHeader>
          <div className="flex items-center space-x-4">
            <div className="h-12 w-12 bg-gray-200 rounded-lg animate-pulse" />
            <div className="space-y-2 flex-1">
              <div className="h-4 w-32 bg-gray-200 rounded animate-pulse" />
              <div className="h-8 w-24 bg-gray-200 rounded animate-pulse" />
            </div>
          </div>
        </CardHeader>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={`${className} mb-6 border-red-200 bg-red-50/50`}>
        <CardHeader>
          <div className="flex items-start space-x-3">
            <svg
              className="h-5 w-5 text-red-500 mt-0.5"
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
            <div>
              <p className="text-sm font-medium text-red-800">
                Error Loading Credits
              </p>
              <p className="text-sm text-red-600 mt-1">{error}</p>
            </div>
          </div>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card
      className={`${className} mb-6 border-[#2C7FB8]/20 bg-gradient-to-br from-white to-[#FFF2C2]/10`}
    >
      <CardHeader>
        <CardTitle className="text-sm font-medium text-[#253494]/70">
          Available Credits
          {showOrganizationName && resolvedOrgName && ` · ${resolvedOrgName}`}
        </CardTitle>
        <div className="flex items-baseline space-x-2">
          <p className="text-4xl font-bold text-[#253494]">
            {creditBalance?.toLocaleString() ?? "0"}
          </p>
          <p className="text-sm text-[#2C7FB8]">credits</p>
        </div>
      </CardHeader>
    </Card>
  );
}

export { CreditBalance, CreditBalanceMeta };
