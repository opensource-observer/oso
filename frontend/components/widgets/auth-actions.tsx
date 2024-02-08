import React, { ReactNode } from "react";
import { Provider } from "@supabase/supabase-js";
import { supabaseClient } from "../../lib/clients/supabase";
import { assertNever, spawn } from "../../lib/common";

type AuthActionType = "signInWithOAuth" | "signOut";
const DEFAULT_PROVIDER: Provider = "google";

type AuthActionsProps = React.PropsWithChildren<{
  className?: string; // Plasmic CSS class
  children?: ReactNode; // Show this
  actionType?: AuthActionType; // Selector for what to do on click
  provider?: Provider;
}>;

function AuthActions(props: AuthActionsProps) {
  const { className, children, actionType, provider } = props;
  const signInWithOAuth = async () => {
    console.log("Click sign in");
    const { data, error } = await supabaseClient.auth.signInWithOAuth({
      provider: provider ?? DEFAULT_PROVIDER,
      options: {
        queryParams: {
          access_type: "offline",
          prompt: "consent",
        },
      },
    });
    console.log("!!!");
    console.log(data, error);
  };
  const signOut = async () => {
    console.log("Click sign out");
    const { error } = await supabaseClient.auth.signOut();
    console.log("!!!");
    console.log(error);
  };
  const clickHandler = async () => {
    if (!actionType) {
      console.warn("Select an actionType first");
      return;
    }
    switch (actionType) {
      case "signInWithOAuth":
        await signInWithOAuth();
        break;
      case "signOut":
        await signOut();
        break;
      default:
        console.warn("Unrecognized action: ", actionType);
        assertNever(actionType);
    }
  };

  return (
    <div className={className} onClick={() => spawn(clickHandler())}>
      {children}
    </div>
  );
}

export { AuthActions };
