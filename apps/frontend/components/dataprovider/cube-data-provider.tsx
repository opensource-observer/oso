import React from "react";
import { useCubeQuery } from "@cubejs-client/react";
import { RegistrationProps } from "../../lib/types/plasmic";
import {
  DataProviderView,
  CommonDataProviderRegistration,
} from "./provider-view";
import { cubeApi } from "../../lib/clients/cube";
import type { CommonDataProviderProps } from "./provider-view";

/**
 * Generic query component focused on providing metrics data to visualiation components
 */
type CubeDataProviderProps = CommonDataProviderProps & {
  query: any;
};

/**
 * Plasmic component registration
 */
const CubeDataProviderRegistration: RegistrationProps<CubeDataProviderProps> = {
  ...CommonDataProviderRegistration,
  query: {
    type: "object",
    helpText: "Query passed directly to Cube.dev",
  },
};

function CubeDataProvider(props: CubeDataProviderProps) {
  const { resultSet, isLoading, error, progress } = useCubeQuery(props.query, {
    cubeApi,
  });

  !isLoading && console.log(props, resultSet, error, progress);
  return (
    <DataProviderView
      {...props}
      formattedData={resultSet}
      loading={isLoading}
      error={error}
    />
  );
}

export { CubeDataProviderRegistration, CubeDataProvider };
export type { CubeDataProviderProps };
