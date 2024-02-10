import { ReactNode } from "react";
import { useAsync } from "react-use";
import {
  CommonDataProviderProps,
  CommonDataProviderRegistration,
  DataProviderView,
} from "./provider-view";
import { RegistrationProps } from "../../lib/types/plasmic";
import { logger } from "../../lib/logger";
import { supabaseClient } from "../../lib/clients/supabase";

const DEFAULT_PLASMIC_VARIABLE = "auth";

type AuthRouterProps = CommonDataProviderProps & {
  noAuthChildren?: ReactNode;
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
    testNoAuth,
  } = props;
  const key = variableName ?? DEFAULT_PLASMIC_VARIABLE;

  const {
    value: data,
    error,
    loading,
  } = useAsync(async () => {
    if (useTestData) {
      return testData;
    }
    const {
      data: { user },
    } = await supabaseClient.auth.getUser();
    const {
      data: { session },
    } = await supabaseClient.auth.getSession();
    console.log("User: ", user);
    console.log("Session: ", session);
    return {
      user,
      session,
      supabase: supabaseClient,
    };
  }, []);

  // Error messages are currently silently logged
  if (!loading && error) {
    logger.error(error);
  }

  // Show unauthenticated view
  if (testNoAuth || (!loading && !data?.user)) {
    return <div className={className}>{noAuthChildren}</div>;
  }

  return (
    <DataProviderView
      {...props}
      variableName={key}
      formattedData={data}
      loading={loading}
      error={error}
    />
  );
}

export { AuthRouter, AuthRouterRegistration };
export type { AuthRouterProps };
