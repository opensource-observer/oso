"use client";

import { ApolloSandbox } from "@apollo/sandbox/react";
import { useAsync } from "react-use";
import { DOMAIN } from "../../lib/config";
import { supabaseClient } from "../../lib/clients/supabase";

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
  const token = data?.session?.access_token;
  const headers = token
    ? { Authorization: `Bearer ${token}` }
    : ({} as Record<string, string>);

  return (
    <ApolloSandbox
      className={props.className}
      initialEndpoint={API_URL.toString()}
      initialState={{
        sharedHeaders: headers,
      }}
    />
  );
}
export { EmbeddedSandbox };
