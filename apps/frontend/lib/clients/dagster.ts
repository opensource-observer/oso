import { ApolloClient, HttpLink, InMemoryCache } from "@apollo/client";
import { DAGSTER_GRAPHQL_URL } from "@/lib/config";

function getDagsterClient() {
  return new ApolloClient({
    cache: new InMemoryCache(),
    link: new HttpLink({
      uri: DAGSTER_GRAPHQL_URL,
    }),
  });
}

export { getDagsterClient };
