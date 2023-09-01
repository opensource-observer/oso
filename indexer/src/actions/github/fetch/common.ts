import { PageInfo } from "../../../events/github/unpaginate.js";

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

export type PaginatableEdges<T> = {
  edges: T[];
  pageInfo: PageInfo;
};
