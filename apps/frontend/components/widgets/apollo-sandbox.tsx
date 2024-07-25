"use client";

import { ApolloSandbox } from "@apollo/sandbox/react";
import { DOMAIN } from "../../lib/config";

const API_PROTOCOL = "https://";
const API_BASE = API_PROTOCOL + DOMAIN;
const API_PATH = "/api/graphql";
const API_URL = new URL(API_PATH, API_BASE);

type EmbeddedSandboxProps = {
  className?: string;
};

function EmbeddedSandbox(props: EmbeddedSandboxProps) {
  return (
    <ApolloSandbox
      className={props.className}
      initialEndpoint={API_URL.toString()}
    />
  );
}
export { EmbeddedSandbox };
