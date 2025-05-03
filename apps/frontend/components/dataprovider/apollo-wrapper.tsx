"use client";

import { ApolloLink, HttpLink } from "@apollo/client";
import {
  ApolloNextAppProvider,
  InMemoryCache,
  ApolloClient,
  SSRMultipartLink,
} from "@apollo/experimental-nextjs-app-support";
import { useAsync } from "react-use";
import { supabaseClient } from "../../lib/clients/supabase";
import { DB_GRAPHQL_URL } from "../../lib/config";

function makeMakeClient(token?: string) {
  const makeLink = () => {
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
  return makeClient;
}

function ApolloWrapper({ children }: React.PropsWithChildren) {
  const { value: data } = useAsync(async () => {
    const {
      data: { session },
    } = await supabaseClient.auth.getSession();
    return {
      session,
    };
  }, []);
  const token = data?.session?.access_token;
  return (
    <ApolloNextAppProvider makeClient={makeMakeClient(token)}>
      {children}
    </ApolloNextAppProvider>
  );
}

export { ApolloWrapper };
