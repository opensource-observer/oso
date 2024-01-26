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

type AuthContextProps = CommonDataProviderProps & {
  noAuthChildren?: ReactNode;
  testNoAuth?: boolean;
};

const AuthContextRegistration: RegistrationProps<AuthContextProps> = {
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

function AuthContext(props: AuthContextProps) {
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

  const { value, error, loading } = useAsync(async () => {
    if (useTestData) {
      return testData;
    }
    const {
      data: { user },
    } = await supabaseClient.auth.getUser();
    return user;
  }, []);

  // Error messages are currently silently logged
  if (!loading && error) {
    logger.error(error);
  }

  // Show unauthenticated view
  if (testNoAuth || (!loading && !value)) {
    return <div className={className}>{noAuthChildren}</div>;
  }

  return (
    <DataProviderView
      {...props}
      variableName={key}
      formattedData={value}
      loading={loading}
      error={error}
    />
  );
}

export { AuthContext, AuthContextRegistration };
export type { AuthContextProps };
