"use client";

import { createContext, useContext, useState, useEffect } from "react";
import { ADT } from "ts-adt";
import { createBrowserClient } from "@/lib/supabase/browser";
import { Session, AuthError, SupabaseClient } from "@supabase/supabase-js";
import { spawn } from "@opensource-observer/utils";
import { Database } from "@/lib/types/supabase";

type SupabaseState = ADT<{
  loading: {
    supabaseClient: null;
  };
  loggedIn: {
    supabaseClient: SupabaseClient<Database>;
    session: Session;
    revalidate: () => Promise<void>;
  };
  loggedOut: {
    supabaseClient: SupabaseClient<Database>;
    revalidate: () => Promise<void>;
  };
  error: {
    error: AuthError;
    supabaseClient: SupabaseClient<Database>;
    revalidate: () => Promise<void>;
  };
}>;

/**
type SupabaseState = {
  supabaseClient?: SupabaseClient<Database> | null;
  session?: Session | null;
  revalidate: () => Promise<void>;
  //isLoading?: boolean;
  //error?: Error;
} | null;
*/

const SupabaseContext = createContext<SupabaseState>({ _type: "loading" });
function useSupabaseState() {
  return useContext<SupabaseState>(SupabaseContext);
}

function SupabaseProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<SupabaseState>({ _type: "loading" });

  useEffect(() => {
    const supabaseClient = createBrowserClient();

    const revalidate = async () => {
      const { data, error } = await supabaseClient.auth.getSession();
      if (error) {
        console.warn("Failed to get Supabase session, ", error);
        return setState({ _type: "error", error, supabaseClient, revalidate });
      } else if (!data.session) {
        return setState({ _type: "loggedOut", supabaseClient, revalidate });
      }
      setState({
        _type: "loggedIn",
        supabaseClient,
        session: data.session,
        revalidate,
      });
    };

    spawn(revalidate());

    const {
      data: { subscription },
    } = supabaseClient.auth.onAuthStateChange((_event, session) => {
      if (!session) {
        return setState({ _type: "loggedOut", supabaseClient, revalidate });
      }
      setState({
        _type: "loggedIn",
        supabaseClient,
        session,
        revalidate,
      });
    });

    return () => subscription.unsubscribe();
  }, []);

  return (
    <SupabaseContext.Provider value={state}>
      {children}
    </SupabaseContext.Provider>
  );
}

export { SupabaseContext, useSupabaseState, SupabaseProvider };
