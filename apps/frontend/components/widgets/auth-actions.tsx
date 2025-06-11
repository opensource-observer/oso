import React, { ReactNode } from "react";
import { Provider } from "@supabase/supabase-js";
import { useRouter, usePathname } from "next/navigation";
import { usePostHog } from "posthog-js/react";
import { assertNever, ensure, spawn } from "@opensource-observer/utils";
import { useSupabaseState } from "@/components/hooks/supabase";
import { RegistrationProps } from "@/lib/types/plasmic";
import { NODE_ENV, DOMAIN } from "@/lib/config";

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
  const supabaseState = useSupabaseState();
  const rawRedirectPath = redirectOnComplete ?? path;
  const redirectPath = rawRedirectPath.startsWith("/")
    ? rawRedirectPath
    : `/${rawRedirectPath}`;
  const redirect = `${PROTOCOL}://${DOMAIN}${redirectPath}`;
  console.log(redirect);
  const signInWithOAuth = async () => {
    const ensureProvider = provider ?? DEFAULT_PROVIDER;
    const ensureScopes = scopes ?? DEFAULT_SCOPES[ensureProvider];
    const ensureSupabaseClient = ensure(
      supabaseState?.supabaseClient,
      "Supabase client not initialized yet",
    );
    posthog.capture("user_login", {
      redirect,
      scopes: ensureScopes,
      provider: ensureProvider,
    });
    const { data, error } = await ensureSupabaseClient.auth.signInWithOAuth({
      provider: ensureProvider,
      options: {
        redirectTo: redirect,
        scopes: ensureScopes,
        queryParams: {
          access_type: "offline",
          prompt: "consent",
        },
      },
    });
    await supabaseState?.revalidate();
    console.log("Supabase signin:", data, error);
  };

  const signOut = async () => {
    const ensureSupabaseClient = ensure(
      supabaseState?.supabaseClient,
      "Supabase client not initialized yet",
    );
    const { error } = await ensureSupabaseClient.auth.signOut();
    // Make sure we dis-associate the logged in user
    posthog.capture("user_logout", {
      redirect: redirectOnComplete,
    });
    posthog.reset();
    await supabaseState?.revalidate();
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
