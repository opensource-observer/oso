import { GraphQLClient } from "graphql-request";

export function graphQLClient(
  token: string,
  graphQLApiUrl: string = "https://api.github.com/graphql",
) {
  return new GraphQLClient(graphQLApiUrl, {
    headers: {
      authorization: `Bearer ${token}`,
    },
  });
}
