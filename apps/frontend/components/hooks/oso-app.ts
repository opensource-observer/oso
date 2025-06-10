"use client";

import { useSupabaseState } from "@/components/hooks/supabase";
import { OsoAppClient } from "@/lib/clients/oso-app/oso-app";

function useOsoAppClient() {
  const supabaseState = useSupabaseState();
  return {
    client: supabaseState?.supabaseClient
      ? new OsoAppClient(supabaseState.supabaseClient)
      : null,
  };
}

export { useOsoAppClient };
