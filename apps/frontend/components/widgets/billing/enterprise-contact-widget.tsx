"use client";

import React, { useEffect, useState } from "react";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import { useSupabaseState } from "@/components/hooks/supabase";
import { OsoAppClient } from "@/lib/clients/oso-app/oso-app";
import { logger } from "@/lib/logger";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface EnterpriseContactProps {
  className?: string;
  organizationName?: string;
  previewMode?: boolean;
  previewSupportUrl?: string;
  previewContactEmail?: string;
}

const EnterpriseContactMeta: CodeComponentMeta<EnterpriseContactProps> = {
  name: "EnterpriseContact",
  description:
    "Display enterprise support contact information for billing inquiries",
  props: {
    organizationName: {
      type: "string",
      helpText:
        "Organization name to fetch contact info for (if not provided, uses user's first organization)",
    },
    previewMode: {
      type: "boolean",
      defaultValue: false,
      helpText: "Enable preview mode with mock data for Plasmic testing",
    },
    previewSupportUrl: {
      type: "string",
      defaultValue: "https://oso.xyz/discord",
      helpText: "Mock support URL for preview mode",
    },
    previewContactEmail: {
      type: "string",
      defaultValue: "enterprise@oso.xyz",
      helpText: "Mock contact email for preview mode",
    },
  },
};

function EnterpriseContact(props: EnterpriseContactProps) {
  const {
    className,
    organizationName,
    previewMode = false,
    previewSupportUrl = "https://oso.xyz/discord",
    previewContactEmail = "enterprise@oso.xyz",
  } = props;

  const supabaseState = useSupabaseState();
  const [client, setClient] = useState<OsoAppClient | null>(null);
  const [loading, setLoading] = useState(!previewMode);
  const [error, setError] = useState<string | null>(null);
  const [supportUrl, setSupportUrl] = useState<string | null>(null);
  const [contactEmail, setContactEmail] = useState<string | null>(null);

  const session =
    supabaseState._type === "loggedIn" ? supabaseState.session : null;

  useEffect(() => {
    if (supabaseState?.supabaseClient && !previewMode) {
      setClient(new OsoAppClient(supabaseState.supabaseClient));
    }
  }, [supabaseState, previewMode]);

  useEffect(() => {
    if (previewMode) {
      setSupportUrl(previewSupportUrl);
      setContactEmail(previewContactEmail);
      setLoading(false);
      return;
    }

    const loadContactInfo = async () => {
      if (!client || !session) {
        setLoading(false);
        return;
      }

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
            setError(
              "You must be part of an organization to view contact info",
            );
            return;
          }
          targetOrg = await client.getOrganizationById({
            orgId: userOrganizations[0].id,
          });
        }

        setSupportUrl(targetOrg.enterprise_support_url || null);
        setContactEmail(targetOrg.billing_contact_email || null);
      } catch (err) {
        logger.error("Error loading enterprise contact info:", err);
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load contact information",
        );
      } finally {
        setLoading(false);
      }
    };

    void loadContactInfo();
  }, [
    client,
    session,
    organizationName,
    previewMode,
    previewSupportUrl,
    previewContactEmail,
  ]);

  if (!previewMode && !session) {
    return (
      <div className={`${className} mb-8`}>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-start">
              <svg
                className="h-5 w-5 text-amber-400 mt-0.5 mr-3 shrink-0"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
              <p className="text-sm text-gray-700">
                Please log in to view contact information.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (loading) {
    return (
      <div className={`${className} mb-8`}>
        <Card>
          <CardHeader>
            <div className="h-6 w-48 bg-gray-200 rounded animate-pulse" />
            <div className="h-4 w-64 bg-gray-200 rounded animate-pulse mt-2" />
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="h-10 w-full bg-gray-200 rounded animate-pulse" />
              <div className="h-10 w-full bg-gray-200 rounded animate-pulse" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`${className} mb-8`}>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-start">
              <svg
                className="h-5 w-5 text-red-400 mt-0.5 mr-3 shrink-0"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className={`${className} mb-8`}>
      <Card className="border-[#41B6C4]/30 bg-gradient-to-br from-white to-[#99D8C9]/5">
        <CardHeader>
          <CardTitle className="text-[#253494]">Enterprise Support</CardTitle>
          <CardDescription className="text-[#253494]/70">
            Need help with your account or have billing questions? Our
            enterprise support team is here to assist you.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {supportUrl && (
              <Button
                asChild
                size="lg"
                variant="outline"
                className="border-[#2C7FB8] text-[#253494] hover:bg-[#41B6C4]/5 hover:border-[#253494] justify-start h-auto py-5 flex-col items-start"
              >
                <a
                  href={supportUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full"
                >
                  <div className="flex items-center w-full mb-2">
                    <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-[#41B6C4]/15 mr-3">
                      <svg
                        className="h-5 w-5 text-[#253494]"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                        />
                      </svg>
                    </div>
                    <svg
                      className="h-4 w-4 ml-auto text-[#253494]/50"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                      />
                    </svg>
                  </div>
                  <div className="w-full text-left">
                    <div className="font-semibold text-sm">Support Channel</div>
                    <div className="text-xs text-[#253494]/60 mt-1">
                      Get help from our team
                    </div>
                  </div>
                </a>
              </Button>
            )}

            {contactEmail && (
              <Button
                asChild
                size="lg"
                variant="outline"
                className="border-[#2C7FB8] text-[#253494] hover:bg-[#41B6C4]/5 hover:border-[#253494] justify-start h-auto py-5 flex-col items-start"
              >
                <a href={`mailto:${contactEmail}`} className="w-full">
                  <div className="flex items-center w-full mb-2">
                    <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-[#41B6C4]/15 mr-3">
                      <svg
                        className="h-5 w-5 text-[#253494]"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                        />
                      </svg>
                    </div>
                  </div>
                  <div className="w-full text-left">
                    <div className="font-semibold text-sm">Billing Contact</div>
                    <div className="text-xs text-[#253494]/60 mt-1 truncate">
                      {contactEmail}
                    </div>
                  </div>
                </a>
              </Button>
            )}

            {!supportUrl && !contactEmail && (
              <div className="col-span-full text-center py-8">
                <svg
                  className="h-12 w-12 mx-auto text-[#253494]/20 mb-3"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <p className="text-sm text-[#253494]/60">
                  No contact information available. Please contact your account
                  administrator.
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export { EnterpriseContact, EnterpriseContactMeta };
