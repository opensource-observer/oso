import React, { ReactNode } from "react";
import { Provider } from "@supabase/supabase-js";
import { useRouter, usePathname } from "next/navigation";
import { usePostHog } from "posthog-js/react";
import { assertNever, spawn } from "@opensource-observer/utils";
import { supabaseClient } from "../../lib/clients/supabase";
import { RegistrationProps } from "../../lib/types/plasmic";
import { NODE_ENV, DOMAIN } from "../../lib/config";

type AuthActionType = "signInWithOAuth" | "signOut";
const DEFAULT_PROVIDER: Provider = "google";
const PROTOCOL = NODE_ENV === "production" ? "https" : "http";
const DEFAULT_SCOPES: Partial<Record<Provider, string>> = {
  google: "openid https://www.googleapis.com/auth/userinfo.email",
  //"openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/bigquery",
  github: "",
};

type AuthActionsProps = {
  className?: string; // Plasmic CSS class
  children?: ReactNode; // Show this
  actionType?: AuthActionType; // Selector for what to do on click
  provider?: Provider;
  scopes?: string;
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
  scopes: {
    type: "string",
    helpText: "See Supabase scopes type",
  },
  redirectOnComplete: {
    type: "string",
    helpText: "Must be an absolute path from this domain (e.g. /login)",
  },
};

function AuthActions(props: AuthActionsProps) {
  const {
    className,
    children,
    actionType,
    provider,
    scopes,
    redirectOnComplete,
  } = props;
  const posthog = usePostHog();
  const router = useRouter();
  const path = usePathname();
  const signInWithOAuth = async () => {
    const redirect = `${PROTOCOL}://${DOMAIN}/${redirectOnComplete ?? path}`;
    const ensureProvider = provider ?? DEFAULT_PROVIDER;
    const { data, error } = await supabaseClient.auth.signInWithOAuth({
      provider: ensureProvider,
      options: {
        redirectTo: redirect,
        scopes: scopes ?? DEFAULT_SCOPES[ensureProvider],
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
    // Make sure we dis-associate the logged in user
    posthog.reset();
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
