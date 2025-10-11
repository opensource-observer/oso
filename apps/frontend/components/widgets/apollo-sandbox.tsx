"use client";

import { ApolloSandbox } from "@apollo/sandbox/react";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import { ThemeProvider } from "next-themes";
import { useTheme } from "next-themes";
import { useSupabaseState } from "@/components/hooks/supabase";
import { useOsoAppClient } from "@/components/hooks/oso-app";
import { DOMAIN } from "@/lib/config";
import { useState, useCallback, useRef, useEffect, useMemo } from "react";
import { useAsync } from "react-use";
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

type EmbeddedSandboxProps = {
  className?: string;
};

function EmbeddedSandboxContent(props: EmbeddedSandboxProps) {
  const { className } = props;
  const { resolvedTheme } = useTheme();
  const supabaseState = useSupabaseState();
  const { client } = useOsoAppClient();

  const clientRef = useRef(client);
  useEffect(() => {
    clientRef.current = client;
  }, [client]);

  const [selectedOrg, setSelectedOrg] = useState<string>("");
  const [open, setOpen] = useState(false);

  const { value: organizations } = useAsync(async () => {
    if (supabaseState._type !== "loggedIn" || !clientRef.current) return [];

    try {
      return await clientRef.current.getMyOrganizations();
    } catch (error) {
      logger.error("Error fetching organizations:", error);
      return [];
    }
  }, [supabaseState._type]);

  useEffect(() => {
    if (organizations?.length && !selectedOrg) {
      setSelectedOrg(organizations[0].org_name);
    }
  }, [organizations, selectedOrg]);

  const { value: token } = useAsync(async () => {
    if (!selectedOrg || supabaseState._type !== "loggedIn") return null;

    try {
      const response = await fetch(
        `/api/v1/jwt?orgName=${encodeURIComponent(selectedOrg)}`,
      );
      if (!response.ok) return null;

      const data = await response.json();
      return data.token;
    } catch (error) {
      logger.error("Error fetching JWT token:", error);
      return null;
    }
  }, [selectedOrg, supabaseState._type]);

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

  const selectedOrgName = useMemo(
    () => organizations?.find((org) => org.org_name === selectedOrg)?.org_name,
    [organizations, selectedOrg],
  );

  return (
    <div className="relative h-full w-full">
      <ApolloSandbox
        className={className}
        initialEndpoint={API_URL.toString()}
        handleRequest={handleRequest}
      />

      {organizations && organizations.length > 0 && (
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
  props: {},
  importPath: "@/components/widgets/apollo-sandbox",
};

export { EmbeddedSandbox, EmbeddedSandboxMeta };
