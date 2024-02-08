import React, { ReactNode } from "react";
import { Provider } from "@supabase/supabase-js";
import { supabaseClient } from "../../lib/clients/supabase";
import { assertNever, spawn } from "../../lib/common";
import { NODE_ENV, DOMAIN } from "../../lib/config";

type AuthActionType = "signInWithOAuth" | "signOut";
const DEFAULT_PROVIDER: Provider = "google";
const URL_AFTER_LOGIN =
  NODE_ENV === "production"
    ? `https://${DOMAIN}/settings/profile`
    : `http://${DOMAIN}/settings/profile`;

type AuthActionsProps = React.PropsWithChildren<{
  className?: string; // Plasmic CSS class
  children?: ReactNode; // Show this
  actionType?: AuthActionType; // Selector for what to do on click
  provider?: Provider;
}>;

function AuthActions(props: AuthActionsProps) {
  const { className, children, actionType, provider } = props;
  const signInWithOAuth = async () => {
    const { data, error } = await supabaseClient.auth.signInWithOAuth({
      provider: provider ?? DEFAULT_PROVIDER,
      options: {
        redirectTo: URL_AFTER_LOGIN,
        scopes: "openid https://www.googleapis.com/auth/userinfo.email",
        //"openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/bigquery",
        queryParams: {
          access_type: "offline",
          prompt: "consent",
        },
      },
    });
    console.log("Supabase signin:", data, error);
  };

  const signOut = async () => {
    const { error } = await supabaseClient.auth.signOut();
    console.log("Supabase signout: ", error);
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
