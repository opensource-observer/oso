export type GithubGraphQLResponse<T> = T & {
  rateLimit: {
    remaining: number;
    limit: number;
    cost: number;
    resetAt: number;
  };
};

export type GraphQLNode<T> = {
  node: T;
};

export type Actor = {
  login: string;
};
