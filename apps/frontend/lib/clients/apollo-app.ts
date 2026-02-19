import { HttpLink } from "@apollo/client";
import {
  registerApolloClient,
  ApolloClient,
  InMemoryCache,
} from "@apollo/client-integration-nextjs";
import { APP_GRAPHQL_URL } from "@/lib/config";
import { headers } from "next/headers";

export const { getClient, query, PreloadQuery } = registerApolloClient(() => {
  const headerInstance = headers();
  return new ApolloClient({
    cache: new InMemoryCache(),
    link: new HttpLink({
      uri: APP_GRAPHQL_URL,
      credentials: "same-origin",
      headers: {
        cookie: headerInstance.get("cookie") ?? "",
      },
    }),
  });
});
