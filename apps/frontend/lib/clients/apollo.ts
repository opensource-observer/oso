import { ApolloClient, InMemoryCache, HttpLink } from "@apollo/client";
import { registerApolloClient } from "@apollo/client-integration-nextjs";
import { DB_GRAPHQL_URL, OSO_API_KEY } from "@/lib/config";

const { getClient: getApolloClient } = registerApolloClient(() => {
  return new ApolloClient({
    cache: new InMemoryCache(),
    link: new HttpLink({
      uri: DB_GRAPHQL_URL,
      headers: {
        Authorization: `Bearer ${OSO_API_KEY}`,
      },
    }),
  });
});

export { getApolloClient };
