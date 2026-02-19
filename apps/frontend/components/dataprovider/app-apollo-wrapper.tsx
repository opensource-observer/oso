"use client";

import { ApolloLink, HttpLink } from "@apollo/client";
import {
  ApolloNextAppProvider,
  InMemoryCache,
  ApolloClient,
  SSRMultipartLink,
} from "@apollo/client-integration-nextjs";
import { APP_GRAPHQL_URL } from "@/lib/config";

function AppApolloWrapper({ children }: React.PropsWithChildren) {
  const makeClient = () => {
    const httpLink = new HttpLink({
      uri: APP_GRAPHQL_URL,
      credentials: "same-origin",
    });

    return new ApolloClient({
      cache: new InMemoryCache(),
      link:
        typeof window === "undefined"
          ? ApolloLink.from([
              new SSRMultipartLink({ stripDefer: true }),
              httpLink,
            ])
          : httpLink,
    });
  };

  return (
    <ApolloNextAppProvider makeClient={makeClient}>
      {children}
    </ApolloNextAppProvider>
  );
}

export { AppApolloWrapper };
