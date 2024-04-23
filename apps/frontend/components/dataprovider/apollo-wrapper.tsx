"use client";

import { ApolloLink, HttpLink, useApolloClient } from "@apollo/client";
import {
  ApolloNextAppProvider,
  NextSSRInMemoryCache,
  NextSSRApolloClient,
  SSRMultipartLink,
} from "@apollo/experimental-nextjs-app-support/ssr";
import { onError } from "@apollo/client/link/error";
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
  const token = userToken;
  //console.log(userToken);
  const httpLink = new HttpLink({
    uri: DB_GRAPHQL_URL,
    headers: token
      ? {
          Authorization: `Bearer ${token}`,
        }
      : {},
  });
  return httpLink;
}

const errorLink = onError(({ graphQLErrors, networkError }) => {
  if (graphQLErrors)
    graphQLErrors.forEach(({ message, locations, path }) =>
      console.log(
        `[GraphQL error]: Message: ${message}, Location: ${locations}, Path: ${path}`,
      ),
    );
  if (networkError) {
    console.warn(`[Network error]: ${networkError}`);
  }
});

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
            errorLink,
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
