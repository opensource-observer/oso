"use client";

import { useSupabaseState } from "@/components/hooks/supabase";
import { OsoAppClient } from "@/lib/clients/oso-app/oso-app";
import { useMemo } from "react";

function useOsoAppClient() {
  const supabaseState = useSupabaseState();
  const osoAppClient = useMemo(
    () => ({
      client: supabaseState?.supabaseClient
        ? new OsoAppClient(supabaseState.supabaseClient)
        : null,
    }),
    [supabaseState?.supabaseClient],
  );
  return osoAppClient;
}

export { useOsoAppClient };
