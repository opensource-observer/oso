import { ReactNode } from "react";
import { usePostHog } from "posthog-js/react";
import {
  CommonDataProviderProps,
  CommonDataProviderRegistration,
  DataProviderView,
} from "@/components/dataprovider/provider-view";
import { RegistrationProps } from "@/lib/types/plasmic";
import { useSupabaseState } from "@/components/hooks/supabase";

const DEFAULT_PLASMIC_VARIABLE = "auth";

type AuthRouterProps = CommonDataProviderProps & {
  noAuthChildren?: ReactNode;
  ignoreNoAuth?: boolean;
  testNoAuth?: boolean;
};

const AuthRouterRegistration: RegistrationProps<AuthRouterProps> = {
  ...CommonDataProviderRegistration,
  noAuthChildren: {
    type: "slot",
    defaultValue: {
      type: "text",
      value: "Placeholder",
    },
  },
  ignoreNoAuth: {
    type: "boolean",
    advanced: true,
    helpText: "Always render children",
  },
  testNoAuth: {
    type: "boolean",
    editOnly: true,
    advanced: true,
  },
};

function AuthRouter(props: AuthRouterProps) {
  // These props are set in the Plasmic Studio
  const {
    className,
    variableName,
    useTestData,
    noAuthChildren,
    ignoreNoAuth,
    testNoAuth,
  } = props;
  const key = variableName ?? DEFAULT_PLASMIC_VARIABLE;
  const supabaseState = useSupabaseState();
  const posthog = usePostHog();

  if (!useTestData && supabaseState._type === "loggedIn") {
    const user = supabaseState.session.user;
    posthog?.identify(user.id, {
      name: user.user_metadata?.name,
      email: user.email,
    });
  }
  //console.log("AuthRouter: ", data);

  // Show unauthenticated view
  if (
    testNoAuth ||
    (!useTestData && !ignoreNoAuth && supabaseState._type === "loggedOut")
  ) {
    return <div className={className}>{noAuthChildren}</div>;
  }

  return (
    <DataProviderView
      {...props}
      variableName={key}
      formattedData={{
        user:
          supabaseState._type === "loggedIn"
            ? supabaseState.session.user
            : null,
        session:
          supabaseState._type === "loggedIn" ? supabaseState.session : null,
        supabase: supabaseState.supabaseClient,
      }}
      loading={supabaseState._type === "loading"}
      error={supabaseState._type === "error" ? supabaseState.error : null}
    />
  );
}

export { AuthRouter, AuthRouterRegistration };
export type { AuthRouterProps };
