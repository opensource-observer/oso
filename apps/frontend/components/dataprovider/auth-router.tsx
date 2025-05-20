import { ReactNode } from "react";
import { usePostHog } from "posthog-js/react";
import {
  CommonDataProviderProps,
  CommonDataProviderRegistration,
  DataProviderView,
} from "./provider-view";
import { RegistrationProps } from "../../lib/types/plasmic";
import { useSupabaseState } from "../hooks/supabase";

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
    testData,
    noAuthChildren,
    ignoreNoAuth,
    testNoAuth,
  } = props;
  const key = variableName ?? DEFAULT_PLASMIC_VARIABLE;
  const supabaseState = useSupabaseState();
  const posthog = usePostHog();

  const data = useTestData
    ? testData
    : {
        user: supabaseState?.session?.user,
        session: supabaseState?.session,
        supabase: supabaseState?.supabaseClient,
      };

  if (!useTestData && data.user) {
    posthog?.identify(data.user.id, {
      name: data.user.user_metadata?.name,
      email: data.user.email,
    });
  }
  //console.log("AuthRouter: ", data);

  // Show unauthenticated view
  if (testNoAuth || (!ignoreNoAuth && !data?.user)) {
    return <div className={className}>{noAuthChildren}</div>;
  }

  return (
    <DataProviderView
      {...props}
      variableName={key}
      formattedData={data}
      loading={false}
      error={null}
    />
  );
}

export { AuthRouter, AuthRouterRegistration };
export type { AuthRouterProps };
