"use client";

import { createContext, useContext, useState, useEffect } from "react";
import { createNormalSupabaseClient } from "@/lib/clients/supabase";
import { Session, SupabaseClient } from "@supabase/supabase-js";
import { Database } from "@/lib/types/supabase";
import { spawn } from "@opensource-observer/utils";

type SupabaseState = {
  supabaseClient?: SupabaseClient<Database> | null;
  session?: Session | null;
  revalidate: () => Promise<void>;
  //isLoading?: boolean;
  //error?: Error;
} | null;

const SupabaseContext = createContext<SupabaseState>(null);
function useSupabaseState() {
  return useContext<SupabaseState>(SupabaseContext);
}

function SupabaseProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<SupabaseState | null>(null);
  const revalidate = async () => {
    const supabaseClient = createNormalSupabaseClient();
    const { data, error } = await supabaseClient.auth.getSession();
    if (error) {
      console.warn("Failed to get Supabase session, ", error);
    }
    setState({
      supabaseClient: supabaseClient,
      session: data.session,
      revalidate,
    });
  };
  useEffect(() => {
    spawn(revalidate());
  }, []);

  return (
    <SupabaseContext.Provider value={state}>
      {children}
    </SupabaseContext.Provider>
  );
}

export { SupabaseContext, useSupabaseState, SupabaseProvider };
