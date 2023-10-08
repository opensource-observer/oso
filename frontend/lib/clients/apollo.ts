import { ApolloClient, InMemoryCache, HttpLink } from "@apollo/client";
import { registerApolloClient } from "@apollo/experimental-nextjs-app-support/rsc";
import { DB_GRAPHQL_URL } from "../config";

const { getClient: getApolloClient } = registerApolloClient(() => {
  return new ApolloClient({
    cache: new InMemoryCache(),
    link: new HttpLink({
      uri: DB_GRAPHQL_URL,
    }),
  });
});

export { getApolloClient };
