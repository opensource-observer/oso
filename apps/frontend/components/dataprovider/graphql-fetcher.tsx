import {
  CommonDataProviderProps,
  CommonDataProviderRegistration,
  DataProviderView,
} from "@/components/dataprovider/provider-view";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import React from "react";
import useSWR from "swr";

const DEFAULT_PLASMIC_KEY = "osoData";

type CustomError = Error & {
  info: Record<string, any>;
  status: number;
};

interface FetchProps {
  url?: string;
  method?: string;
  body?: string | object;
  headers?: Record<string, string>;
}

type GraphqlFetcherProps = CommonDataProviderProps &
  FetchProps & {
    query?: { query?: string; variables?: object };
    queryKey?: string;
    varOverrides?: object;
  };

/**
 * Tries to return the JSON response, or else returns an object with a text key containing the response body text.
 */
async function performFetch({ url, method, body, headers }: FetchProps) {
  if (!url) {
    throw new Error("Please specify a URL to fetch");
  }

  // Add default headers unless specified
  if (!headers) {
    headers = {};
  }
  const headerNamesLowercase = new Set(
    Object.keys(headers).map((headerName) => headerName.toLowerCase()),
  );
  if (!headerNamesLowercase.has("accept")) {
    headers["Accept"] = "application/json";
  }
  if (body && !headerNamesLowercase.has("content-type")) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(url, {
    method,
    headers,
    body:
      body === undefined
        ? body
        : typeof body === "string"
          ? body
          : JSON.stringify(body),
  });

  const text = await response.text();
  let json: Record<string, any> = { text };

  try {
    json = JSON.parse(text);
  } catch {
    json = { text };
  }

  // @see https://swr.vercel.app/docs/error-handling
  // If the status code is not in the range 200-299,
  // we still try to parse and throw it.
  if (!response.ok) {
    const error = new Error(response.statusText) as CustomError;
    // Attach extra info to the error object.
    error.info = json;
    error.status = response.status;
    throw error;
  }

  return json;
}

function GraphqlFetcher(props: GraphqlFetcherProps) {
  const {
    query,
    url,
    method,
    headers,
    queryKey,
    varOverrides,
    variableName,
    ...rest
  } = props;

  const path = url ? new URL(url).pathname : undefined;

  let fetchProps: FetchProps;
  if (method === "GET") {
    // https://graphql.org/learn/serving-over-http/#get-request-and-parameters
    const params = new URLSearchParams();
    params.set("query", query?.query ?? "{}");
    params.set(
      "variables",
      JSON.stringify({ ...query?.variables, ...varOverrides }),
    );
    fetchProps = {
      url: path ? `${path}?${params.toString()}` : undefined,
      method,
      headers,
    };
  } else {
    fetchProps = {
      body: { ...query, variables: { ...query?.variables, ...varOverrides } },
      url: path,
      method,
      headers,
    };
  }

  const { data, mutate, error, isLoading } = useSWR(
    queryKey || JSON.stringify({ type: "GraphqlFetcher", ...fetchProps }),
    () => {
      if (!query || !url) {
        return;
      }
      return performFetch(fetchProps);
    },
  );
  return (
    <DataProviderView
      {...rest}
      variableName={variableName ?? DEFAULT_PLASMIC_KEY}
      formattedData={{ ...data, revalidate: mutate }}
      loading={isLoading}
      error={error}
    />
  );
}

const graphqlFetcherMeta: CodeComponentMeta<GraphqlFetcherProps> = {
  name: "graphql-fetcher",
  displayName: "GraphQL Fetcher",
  providesData: true,
  props: {
    query: {
      type: "code",
      lang: "graphql",
      headers: (props: GraphqlFetcherProps) => props.headers,
      endpoint: (props: GraphqlFetcherProps) => props.url ?? "",
    },
    varOverrides: {
      type: "object",
      displayName: "Override variables",
      description:
        "Pass in dynamic values for your query variables, as an object of key-values",
    },

    url: {
      type: "string",
      defaultValue: "https://www.oso.xyz/api/v1/osograph",
      description: "Where to fetch the data from",
    },
    method: {
      type: "choice",
      options: [
        "GET",
        "DELETE",
        "CONNECT",
        "HEAD",
        "OPTIONS",
        "POST",
        "PUT",
        "TRACE",
      ],
      defaultValue: "POST",
      description: "Method to use when fetching",
    },
    headers: {
      type: "object",
      description: "Request headers (as JSON object) to send",
    },
    queryKey: {
      type: "string",
      description:
        "A globally unique ID for this query, used for invalidating queries",
      invariantable: true,
    },
    ...CommonDataProviderRegistration,
  },
};

export { GraphqlFetcher, graphqlFetcherMeta };
