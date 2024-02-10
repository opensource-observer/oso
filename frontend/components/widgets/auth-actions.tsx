import React, { ReactNode } from "react";
import { Provider } from "@supabase/supabase-js";
import { useRouter, usePathname } from "next/navigation";
import { supabaseClient } from "../../lib/clients/supabase";
import { RegistrationProps } from "../../lib/types/plasmic";
import { assertNever, spawn } from "../../lib/common";
import { NODE_ENV, DOMAIN } from "../../lib/config";

type AuthActionType = "signInWithOAuth" | "signOut";
const DEFAULT_PROVIDER: Provider = "google";
const PROTOCOL = NODE_ENV === "production" ? "https" : "http";

type AuthActionsProps = {
  className?: string; // Plasmic CSS class
  children?: ReactNode; // Show this
  actionType?: AuthActionType; // Selector for what to do on click
  provider?: Provider;
  redirectOnComplete?: string; // URL to redirect to after completion;
};

const AuthActionsRegistration: RegistrationProps<AuthActionsProps> = {
  children: "slot",
  actionType: {
    type: "choice",
    options: ["signInWithOAuth", "signOut"],
  },
  provider: {
    type: "string",
    helpText: "See Supabase provider type",
  },
  redirectOnComplete: {
    type: "string",
    helpText: "Must be an absolute path from this domain (e.g. /login)",
  },
};

function AuthActions(props: AuthActionsProps) {
  const { className, children, actionType, provider, redirectOnComplete } =
    props;
  const router = useRouter();
  const path = usePathname();
  const signInWithOAuth = async () => {
    const redirect = `${PROTOCOL}://${DOMAIN}/${redirectOnComplete ?? path}`;
    const { data, error } = await supabaseClient.auth.signInWithOAuth({
      provider: provider ?? DEFAULT_PROVIDER,
      options: {
        redirectTo: redirect,
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
    if (redirectOnComplete) {
      router.push(redirectOnComplete);
    } else {
      router.refresh();
    }
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

export { AuthActions, AuthActionsRegistration };
