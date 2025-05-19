import React from "react";
import _ from "lodash";
import useSWR from "swr";
import { RegistrationProps } from "../../lib/types/plasmic";
import {
  CommonDataProviderProps,
  CommonDataProviderRegistration,
  DataProviderView,
} from "./provider-view";
import { useOsoAppClient } from "../hooks/oso-app";

// The name used to pass data into the Plasmic DataProvider
const KEY_PREFIX = "oso";
const genKey = (props: OsoDataProviderProps) =>
  `${KEY_PREFIX}:${JSON.stringify(props)}`;

type DataFetch = {
  method: string;
  args: any;
};

/**
 * OSO app client
 */
type OsoDataProviderProps = CommonDataProviderProps & {
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

const OsoDataProviderRegistration: RegistrationProps<OsoDataProviderProps> = {
  ...CommonDataProviderRegistration,
  dataFetches: {
    type: "object",
    helpText:
      "e.g. { members: { method: 'getOrganizationMembers', args: { orgId: 'ORG_ID_HERE' } } }",
  },
};

function OsoDataProvider(props: OsoDataProviderProps) {
  const { dataFetches, variableName, testData, useTestData } = props;
  const key = variableName ?? genKey(props);
  const { client } = useOsoAppClient();
  const { data, mutate, error, isLoading } = useSWR(key, async () => {
    if (useTestData) {
      return testData;
    } else if (!dataFetches || _.isEmpty(dataFetches)) {
      return;
    } else if (!client) {
      throw new Error("No Supabase client found");
    }
    const result: Record<string, any> = {};
    for (const [key, { method, args }] of Object.entries(dataFetches)) {
      if (!method) {
        throw new Error(`No method provided for data fetch ${name}`);
      }
      if (!args) {
        throw new Error(`No args provided for data fetch ${name}`);
      }
      result[key] = await (client as any)[method](args);
    }
    return result;
  });
  //console.log(data);
  //console.log(JSON.stringify(data, null, 2));
  //console.log(error);

  // Error messages are currently rendered in the component
  if (!dataFetches || _.isEmpty(dataFetches)) {
    return <p>You need to set dataFetches prop</p>;
  }

  return (
    <DataProviderView
      {...props}
      formattedData={{ ...data, revalidate: mutate }}
      loading={isLoading}
      error={error}
    />
  );
}

export { OsoDataProviderRegistration, OsoDataProvider };
export type { OsoDataProviderProps };
