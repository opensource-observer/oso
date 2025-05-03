"use client";

import { ApolloSandbox } from "@apollo/sandbox/react";
import { useAsync } from "react-use";
import { supabaseClient } from "../../lib/clients/supabase";
import { DOMAIN } from "../../lib/config";

const API_PROTOCOL = "https://";
const API_BASE = API_PROTOCOL + DOMAIN;
const API_PATH = "/api/v1/graphql";
const API_URL = new URL(API_PATH, API_BASE);

type EmbeddedSandboxProps = {
  className?: string;
};

function EmbeddedSandbox(props: EmbeddedSandboxProps) {
  const { value: data } = useAsync(async () => {
    const {
      data: { session },
    } = await supabaseClient.auth.getSession();
    return {
      session,
    };
  }, []);
  //console.log(data);
  const token = data?.session?.access_token;
  //console.log("headers", headers);

  return (
    <ApolloSandbox
      className={props.className}
      initialEndpoint={API_URL.toString()}
      handleRequest={(endpointUrl, options) => {
        return fetch(endpointUrl, {
          ...options,
          headers: {
            ...options.headers,
            authorization: `Bearer ${token}`,
          },
        });
      }}
    />
  );
}
export { EmbeddedSandbox };
