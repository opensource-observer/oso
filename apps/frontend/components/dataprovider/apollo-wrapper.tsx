"use client";

import { ApolloLink, HttpLink } from "@apollo/client";
import {
  ApolloNextAppProvider,
  InMemoryCache,
  ApolloClient,
  SSRMultipartLink,
} from "@apollo/experimental-nextjs-app-support";
import { useSupabaseState } from "../hooks/supabase";
import { DB_GRAPHQL_URL } from "../../lib/config";

function ApolloWrapper({ children }: React.PropsWithChildren) {
  const supabaseState = useSupabaseState();
  const makeLink = () => {
    //console.log(userToken);
    const httpLink = new HttpLink({
      uri: DB_GRAPHQL_URL,
      headers: supabaseState?.session?.access_token
        ? {
            Authorization: `Bearer ${supabaseState.session.access_token}`,
          }
        : {},
    });
    return httpLink;
  };

  const makeClient = () => {
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
  };

  return (
    <ApolloNextAppProvider makeClient={makeClient}>
      {children}
    </ApolloNextAppProvider>
  );
}

export { ApolloWrapper };
