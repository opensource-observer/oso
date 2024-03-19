"use client";

import { ApolloLink, HttpLink, useApolloClient } from "@apollo/client";
import {
  ApolloNextAppProvider,
  NextSSRInMemoryCache,
  NextSSRApolloClient,
  SSRMultipartLink,
} from "@apollo/experimental-nextjs-app-support/ssr";
import { DB_GRAPHQL_URL } from "../../lib/config";
import { userToken } from "../../lib/clients/supabase";

// Supabase credentials get populated later on
let initialized = false;
const useEnsureAuth = () => {
  const client = useApolloClient();
  if (!initialized && userToken) {
    client.setLink(makeLink());
    initialized = true;
  }
};

function makeLink() {
  //console.log(userToken);
  const httpLink = new HttpLink({
    uri: DB_GRAPHQL_URL,
    headers: userToken
      ? {
          Authorization: `Bearer ${userToken}`,
        }
      : {},
  });
  return httpLink;
}

function makeClient() {
  const httpLink = makeLink();
  const client = new NextSSRApolloClient({
    cache: new NextSSRInMemoryCache(),
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
