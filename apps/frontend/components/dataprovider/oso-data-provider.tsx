import React from "react";
import _ from "lodash";
import useSWR from "swr";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import {
  CommonDataProviderProps,
  CommonDataProviderRegistration,
  DataProviderView,
} from "@/components/dataprovider/provider-view";
import { useOsoAppClient } from "@/components/hooks/oso-app";

// The name used to pass data into the Plasmic DataProvider
const DEFAULT_PLASMIC_KEY = "osoData";
const KEY_PREFIX = "oso";
const genKey = (props: OsoDataProviderProps) =>
  `${KEY_PREFIX}:${JSON.stringify(props.dataFetches)}`;

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

const OsoDataProviderMeta: CodeComponentMeta<OsoDataProviderProps> = {
  name: "OsoDataProvider",
  description: "OSO data provider",
  props: {
    ...CommonDataProviderRegistration,
    dataFetches: {
      type: "object",
      helpText:
        "e.g. { members: { method: 'getOrganizationMembers', args: { orgId: 'ORG_ID_HERE' } } }",
    },
  },
  providesData: true,
};

function OsoDataProvider(props: OsoDataProviderProps) {
  const { dataFetches, variableName } = props;
  const key = genKey(props);
  const { client } = useOsoAppClient();
  const { data, mutate, error, isLoading } = useSWR(
    client ? key : null,
    async () => {
      if (!dataFetches || _.isEmpty(dataFetches)) {
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
      console.log("OsoDataProvider:", props, data);
      return result;
    },
  );
  //console.log(JSON.stringify(data, null, 2));
  if (error) {
    console.log("OsoDataProvider error:", error);
  }

  // Error messages are currently rendered in the component
  if (!dataFetches || _.isEmpty(dataFetches)) {
    return <p>You need to set dataFetches prop</p>;
  }

  return (
    <DataProviderView
      {...props}
      variableName={variableName ?? DEFAULT_PLASMIC_KEY}
      formattedData={{ ...data, revalidate: mutate }}
      loading={isLoading || client == null}
      error={error}
    />
  );
}

export { OsoDataProvider, OsoDataProviderMeta };
export type { OsoDataProviderProps };
