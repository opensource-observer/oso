"use client";

import { ApolloSandbox } from "@apollo/sandbox/react";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import { ThemeProvider } from "next-themes";
import { useTheme } from "next-themes";
import { useSupabaseState } from "@/components/hooks/supabase";
import { useOsoAppClient } from "@/components/hooks/oso-app";
import { DOMAIN } from "@/lib/config";
import { useEffect, useState, useCallback, useRef } from "react";
import { Check, ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { logger } from "@/lib/logger";

const API_PROTOCOL = DOMAIN.includes("localhost") ? "http://" : "https://";
const API_BASE = API_PROTOCOL + DOMAIN;
const API_PATH = "/api/v1/graphql";
const API_URL = new URL(API_PATH, API_BASE);

type Organization = {
  id: string;
  org_name: string;
};

type EmbeddedSandboxProps = {
  className?: string;
};

async function fetchOrgToken(orgName: string): Promise<string | null> {
  try {
    const response = await fetch(
      `/api/v1/jwt?orgName=${encodeURIComponent(orgName)}`,
    );
    if (!response.ok) return null;

    const data = await response.json();
    return data.token;
  } catch (error) {
    logger.error("Error fetching JWT token:", error);
    return null;
  }
}

function useOrganizations() {
  const supabaseState = useSupabaseState();
  const { client } = useOsoAppClient();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const hasLoadedRef = useRef(false);

  useEffect(() => {
    if (supabaseState._type !== "loggedIn" || !client || hasLoadedRef.current)
      return;

    const loadOrganizations = async () => {
      try {
        const orgs = await client.getMyOrganizations();
        setOrganizations(orgs);
        hasLoadedRef.current = true;
      } catch (error) {
        logger.error("Error fetching organizations:", error);
        setOrganizations([]);
      }
    };

    void loadOrganizations();
  }, [supabaseState._type]);

  useEffect(() => {
    if (supabaseState._type !== "loggedIn") {
      hasLoadedRef.current = false;
      setOrganizations([]);
    }
  }, [supabaseState._type]);

  return organizations;
}

function useOrgToken(orgName: string) {
  const supabaseState = useSupabaseState();
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    if (!orgName || supabaseState._type !== "loggedIn") {
      setToken(null);
      return;
    }

    const loadToken = async () => {
      const newToken = await fetchOrgToken(orgName);
      setToken(newToken);
    };

    void loadToken();
  }, [orgName, supabaseState._type]);

  return token;
}

function EmbeddedSandboxContent(props: EmbeddedSandboxProps) {
  const { className } = props;
  const { resolvedTheme } = useTheme();
  const organizations = useOrganizations();
  const [selectedOrg, setSelectedOrg] = useState<string>("");
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (organizations.length > 0 && !selectedOrg) {
      setSelectedOrg(organizations[0].org_name);
    }
  }, [organizations, selectedOrg]);

  const token = useOrgToken(selectedOrg);
  const tokenRef = useRef<string | null>(null);

  useEffect(() => {
    tokenRef.current = token;
  }, [token]);

  const handleRequest = useCallback(
    (endpointUrl: string, options: RequestInit) => {
      return fetch(endpointUrl, {
        ...options,
        headers: {
          ...options.headers,
          ...(tokenRef.current && {
            authorization: `Bearer ${tokenRef.current}`,
          }),
        },
      });
    },
    [],
  );

  const selectedOrgName = organizations.find(
    (org) => org.org_name === selectedOrg,
  )?.org_name;

  return (
    <div className="relative h-full w-full">
      <ApolloSandbox
        className={className}
        initialEndpoint={API_URL.toString()}
        handleRequest={handleRequest}
      />

      {organizations.length > 0 && (
        <div
          className={cn(
            "absolute bottom-4 right-4 z-50",
            resolvedTheme === "dark" && "dark",
          )}
        >
          <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                role="combobox"
                aria-expanded={open}
                className="w-[240px] justify-between"
              >
                {selectedOrgName || "Select organization..."}
                <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[240px] p-0">
              <Command>
                <CommandInput
                  placeholder="Search organization..."
                  className="h-9"
                />
                <CommandList>
                  <CommandEmpty>No organization found.</CommandEmpty>
                  <CommandGroup>
                    {organizations.map((org) => (
                      <CommandItem
                        key={org.id}
                        value={org.org_name}
                        onSelect={(currentValue) => {
                          setSelectedOrg(
                            currentValue === selectedOrg ? "" : currentValue,
                          );
                          setOpen(false);
                        }}
                      >
                        {org.org_name}
                        <Check
                          className={cn(
                            "ml-auto h-4 w-4",
                            selectedOrg === org.org_name
                              ? "opacity-100"
                              : "opacity-0",
                          )}
                        />
                      </CommandItem>
                    ))}
                  </CommandGroup>
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>
        </div>
      )}
    </div>
  );
}

function EmbeddedSandbox(props: EmbeddedSandboxProps) {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      <EmbeddedSandboxContent {...props} />
    </ThemeProvider>
  );
}

const EmbeddedSandboxMeta: CodeComponentMeta<EmbeddedSandboxProps> = {
  name: "EmbeddedSandbox",
  description: "Apollo GraphQL Sandbox with organization selector",
  props: {
    className: {
      type: "class",
      helpText: "CSS classes to apply to the sandbox",
    },
  },
  importPath: "@/components/widgets/apollo-sandbox",
};

export { EmbeddedSandbox, EmbeddedSandboxMeta };
