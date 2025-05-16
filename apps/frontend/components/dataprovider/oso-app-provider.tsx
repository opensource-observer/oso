import React from "react";
import _ from "lodash";
import useSWR from "swr";
//import { RegistrationProps, RegistrationRefActions } from "../../lib/types/plasmic";
import {
  CommonDataProviderProps,
  CommonDataProviderRegistration,
  DataProviderView,
} from "./provider-view";
import { OsoAppClient } from "../../lib/clients/oso-app";

// The name used to pass data into the Plasmic DataProvider
const KEY_PREFIX = "oso";
const genKey = (props: OsoAppProviderProps) =>
  `${KEY_PREFIX}:${JSON.stringify(props)}`;

type DataFetch = {
  method: string;
  args: any;
};

/**
 * OSO app client
 */
type OsoAppProviderProps = CommonDataProviderProps & {
  /**
   * An object containing the client calls to be made, keyed by a unique name.
   * See OsoAppClient for the available methods and their arguments
   * e.g. {
   *   "members": {
   *     method: "getOrganizationMembers",
   *     args: { orgId: "ORG_ID_HERE" }
   *   }
   * }
   * The results will be returned in an Map with the same keys
   **/
  dataFetches?: { [name: string]: Partial<DataFetch> };
};

const OsoAppProviderRegistration: any = {
  ...CommonDataProviderRegistration,
  clientCalls: {
    type: "object",
    helpText:
      "e.g. { members: { method: 'getOrganizationMembers', args: { orgId: 'ORG_ID_HERE' } } }",
  },
};

const OsoAppProviderRefActions: any = {
  updateMyUserProfile: {
    description: "Update the current user's profile",
    argTypes: [{ name: "args", type: "object" }],
  },
  createApiKey: {
    description: "Create an API key for the current user",
    argTypes: [{ name: "args", type: "object" }],
  },
  createOrganization: {
    description: "Create an organization",
    argTypes: [{ name: "args", type: "object" }],
  },
  addUserToOrganizationByEmail: {
    description: "Add an existing user to an organization by email",
    argTypes: [{ name: "args", type: "object" }],
  },
  changeUserRole: {
    description: "Change a user's role in an organization",
    argTypes: [{ name: "args", type: "object" }],
  },
  removeUserFromOrganization: {
    description: "Remove a user from an organization",
    argTypes: [{ name: "args", type: "object" }],
  },
  deleteOrganization: {
    description: "Deletes an organization",
    argTypes: [{ name: "args", type: "object" }],
  },
};

const OsoAppProvider = React.forwardRef<OsoAppClient>(function _OsoAppProvider(
  props: OsoAppProviderProps,
  ref: React.ForwardedRef<OsoAppClient>,
) {
  const { dataFetches, variableName, testData, useTestData } = props;
  const key = variableName ?? genKey(props);
  const osoClient = new OsoAppClient();
  React.useImperativeHandle(ref, () => osoClient, []);
  const { data, error, isLoading } = useSWR(key, async () => {
    if (useTestData) {
      return testData;
    } else if (!dataFetches || _.isEmpty(dataFetches)) {
      return;
    }
    const promises = new Map<string, Promise<any>>();
    for (const [name, { method, args }] of Object.entries(dataFetches)) {
      if (!method) {
        throw new Error(`No method provided for data fetch ${name}`);
      }
      if (!args) {
        throw new Error(`No args provided for data fetch ${name}`);
      }
      const fn = (osoClient as any)[method];
      if (typeof fn === "function") {
        promises.set(name, fn(args));
      } else {
        throw new Error(`Method ${method} is not a function`);
      }
    }
    return await Promise.all(promises);
  });

  // Error messages are currently rendered in the component
  if (!dataFetches || _.isEmpty(dataFetches)) {
    return <p>You need to set dataFetches prop</p>;
  }

  return (
    <DataProviderView
      {...props}
      formattedData={data}
      loading={isLoading}
      error={error}
    />
  );
});

export { OsoAppProviderRegistration, OsoAppProviderRefActions, OsoAppProvider };
export type { OsoAppProviderProps };
