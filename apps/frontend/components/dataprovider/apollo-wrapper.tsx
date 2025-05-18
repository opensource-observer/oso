"use client";

import { ApolloLink, HttpLink, useApolloClient } from "@apollo/client";
import {
  ApolloNextAppProvider,
  InMemoryCache,
  ApolloClient,
  SSRMultipartLink,
} from "@apollo/experimental-nextjs-app-support";
import { userSession } from "../../lib/clients/supabase";
import { DB_GRAPHQL_URL } from "../../lib/config";

/**
 * You must call this hook in any component that uses Apollo in code client-side
 * This will ensure that the Apollo client eventually gets the correct
 * Supabase credentials, which gets populated later on.
 * This is a workaround for the fact that the Apollo client is initialized
 * before the Supabase client is initialized.
 */
let initialized = false;
const useEnsureAuth = () => {
  const client = useApolloClient();
  if (!initialized && userSession?.access_token) {
    client.setLink(makeLink());
    initialized = true;
  }
};

function makeLink() {
  //console.log(userToken);
  const httpLink = new HttpLink({
    uri: DB_GRAPHQL_URL,
    headers: userSession?.access_token
      ? {
          Authorization: `Bearer ${userSession.access_token}`,
        }
      : {},
  });
  return httpLink;
}

function makeClient() {
  const httpLink = makeLink();
  const client = new ApolloClient({
    cache: new InMemoryCache(),
    link:
      typeof window === "undefined"
        ? ApolloLink.from([
            new SSRMultipartLink({
              stripDefer: true,
            }),
            httpLink,
          ])
        : httpLink,
  });
  return client;
}

function ApolloWrapper({ children }: React.PropsWithChildren) {
  return (
    <ApolloNextAppProvider makeClient={makeClient}>
      {children}
    </ApolloNextAppProvider>
  );
}

export { ApolloWrapper, useEnsureAuth };
