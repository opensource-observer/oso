import React from "react";
import { DataProvider, GlobalActionsProvider } from "@plasmicapp/host";
import { supabaseClient } from "../../lib/clients/supabase";

const CONTEXT_NAME = "auth";
const DATA_NAME = "auth";
type AuthGlobalContextProps = React.PropsWithChildren<{
  testUser?: string;
}>;

function AuthGlobalContext(props: AuthGlobalContextProps) {
  const [user, setUser] = React.useState<any>(null);
  const { children } = props;
  const actions = React.useMemo(
    () => ({
      async signInWithOAuth(_provider: string) {
        const { data, error } = await supabaseClient.auth.signInWithOAuth({
          provider: "google",
          options: {
            queryParams: {
              access_type: "offline",
              prompt: "consent",
            },
          },
        });
        console.log("!!!");
        console.log(data, error);
        const {
          data: { user },
        } = await supabaseClient.auth.getUser();
        setUser(user);
      },
      async signOut() {
        await supabaseClient.auth.signOut();
      },
    }),
    [],
  );

  const data = {
    user,
    supabase: supabaseClient,
  };

  return (
    <GlobalActionsProvider contextName={CONTEXT_NAME} actions={actions}>
      <DataProvider name={DATA_NAME} data={data}>
        {children}
      </DataProvider>
    </GlobalActionsProvider>
  );
}

export { AuthGlobalContext };
