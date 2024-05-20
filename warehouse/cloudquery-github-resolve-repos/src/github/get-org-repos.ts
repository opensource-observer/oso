import {
  GetResponseTypeFromEndpointMethod,
  GetResponseDataTypeFromEndpointMethod,
  RequestError,
} from "@octokit/types";
import { gql, GraphQLClient } from "graphql-request";
import { unpaginate, sleep } from "./unpaginate.js";
import { Octokit } from "octokit";

const getManyReposQuery = gql`
  query getManyRepos($searchStr: String!, $first: Int) {
    rateLimit {
      resetAt
      remaining
      nodeCount
      cost
    }
    search(query: $searchStr, type: REPOSITORY, first: $first) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        ... on Repository {
          nameWithOwner
          isFork
          url
          name
          defaultBranchRef {
            name
          }
        }
      }
    }
  }
`;

const getUserRepos = gql`
  query getUserRepos($name: String!, $cursor: String) {
    rateLimit {
      limit
      cost
      remaining
      resetAt
    }
    user(login: $name) {
      id
      createdAt
      repositories(first: 100, after: $cursor) {
        pageInfo {
          hasNextPage
          endCursor
        }
        edges {
          node {
            nameWithOwner
            isFork
            url
            name
            defaultBranchRef {
              name
            }
          }
        }
      }
    }
  }
`;

const getOrgRepos = gql`
  query getOrgRepos($name: String!, $cursor: String) {
    rateLimit {
      limit
      cost
      remaining
      resetAt
    }
    organization(login: $name) {
      id
      createdAt
      repositories(first: 100, after: $cursor) {
        pageInfo {
          hasNextPage
          endCursor
        }
        edges {
          node {
            nameWithOwner
            isFork
            url
            name
            defaultBranchRef {
              name
            }
          }
        }
      }
    }
  }
`;

interface OrgData {
  rateLimit: {
    limit: number;
    cost: number;
    remaining: number;
    resetAt: string;
  };
  organization: {
    id: string;
    createdAt: string;
    repositories: {
      pageInfo: {
        hasNextPage: boolean;
        endCursor: string;
      };
      edges: [
        {
          node: Repository;
        },
      ];
    };
  };
}

interface UserData {
  rateLimit: {
    limit: number;
    cost: number;
    remaining: number;
    resetAt: string;
  };
  user: {
    id: string;
    createdAt: string;
    repositories: {
      pageInfo: {
        hasNextPage: boolean;
        endCursor: string;
      };
      edges: [
        {
          node: Repository;
        },
      ];
    };
  };
}

interface ManyReposData {
  rateLimit: {
    limit: number;
    cost: number;
    remaining: number;
    resetAt: string;
  };
  search: {
    pageInfo: {
      hasNextPage: boolean;
      endCursor: string;
    };
    nodes: Repository[];
  };
}

export interface Repository {
  nameWithOwner: string;
  url: string;
  name: string;
  isFork: boolean;
  defaultBranchRef: null | {
    name: string;
  };
  starCount: number;
  watcherCount: number;
  forkCount: number;
  license: {
    name: string;
    spdxId: string;
  };
  language: string;
}

export type FullRepository = Repository & {
  id: number;
  nodeId: string;
};

export async function getOwnerRepos(
  client: GraphQLClient,
  ownerName: string,
): Promise<Repository[]> {
  const variables = {
    name: ownerName,
  };

  try {
    const nodes = await unpaginate<OrgData>(client)(
      getOrgRepos,
      "organization.repositories.edges",
      "organization.repositories.pageInfo",
      variables,
    );
    return nodes.map((node: any) => node.node);
  } catch (err) {
    try {
      // Try getting the information as a user
      const nodes = await unpaginate<UserData>(client)(
        getUserRepos,
        "user.repositories.edges",
        "user.repositories.pageInfo",
        variables,
      );
      return nodes.map((node: any) => node.node);
    } catch (tryUserErr) {
      return [];
    }
  }
  //return nodes.map((node: any) => node.node);
}

export async function getOwnerReposRest(
  gh: Octokit,
  ownerName: string,
): Promise<FullRepository[]> {
  try {
    const repos = await gh.paginate(gh.rest.repos.listForOrg, {
      org: ownerName,
      headers: {
        "X-Github-Next-Global-ID": 1,
      },
    });
    return repos.map((r) => {
      return {
        id: r.id,
        url: r.html_url,
        nodeId: r.node_id,
        isFork: r.fork,
        name: r.name,
        nameWithOwner: r.full_name,
        defaultBranchRef: {
          name: r.default_branch || "main",
        },
        starCount: r.stargazers_count || 0,
        watcherCount: r.watchers_count || 0,
        forkCount: r.forks_count || 0,
        license: {
          spdxId: r.license?.spdx_id || "",
          name: r.license?.name || "",
        },
        language: r.language || "",
      };
    });
  } catch (err) {
    try {
      const repos = await gh.paginate(gh.rest.repos.listForUser, {
        username: ownerName,
        headers: {
          "X-Github-Next-Global-ID": 1,
        },
      });
      return repos.map((r) => {
        return {
          id: r.id,
          url: r.html_url,
          nodeId: r.node_id,
          isFork: r.fork,
          name: r.name,
          nameWithOwner: r.full_name,
          defaultBranchRef: {
            name: r.default_branch || "main",
          },
          starCount: r.stargazers_count || 0,
          watcherCount: r.watchers_count || 0,
          forkCount: r.forks_count || 0,
          license: {
            spdxId: r.license?.spdx_id || "",
            name: r.license?.name || "",
          },
          language: r.language || "",
        };
      });
    } catch (tryUserErr) {
      return [];
    }
  }
  //return nodes.map((node: any) => node.node);
}

export async function getManyRepos(
  client: GraphQLClient,
  repoNames: string[],
): Promise<ManyReposData> {
  if (repoNames.length > 100) {
    throw new Error("getManyRepos only handles 100 repos at a time");
  }

  const variables = {
    searchStr: repoNames.map((r) => `repo:${r}`).join(" "),
    first: 100,
  };

  const response = await client.request<ManyReposData>(
    getManyReposQuery,
    variables,
  );
  return response;
  //return nodes.map((node: any) => node.node);
}

interface RateLimit {
  limit: number;
  cost: number;
  remaining: number;
  resetAt: string;
}

type RestRepoResponse = GetResponseTypeFromEndpointMethod<
  Octokit["rest"]["repos"]["get"]
>;
type RestRepoData = GetResponseDataTypeFromEndpointMethod<
  Octokit["rest"]["repos"]["get"]
>;

function restRepoDataToFullRepository(r: RestRepoData): FullRepository {
  return {
    id: r.id,
    url: r.html_url,
    nodeId: r.node_id,
    isFork: r.fork,
    name: r.name,
    nameWithOwner: r.full_name,
    defaultBranchRef: {
      name: r.default_branch || "main",
    },
    starCount: r.stargazers_count || 0,
    watcherCount: r.watchers_count || 0,
    forkCount: r.forks_count || 0,
    license: {
      spdxId: r.license?.spdx_id || "",
      name: r.license?.name || "",
    },
    language: r.language || "",
  };
}

export async function resolveAllReposRest(
  gh: Octokit,
  repoNames: string[],
): Promise<FullRepository[]> {
  console.log("calling resolveAllReposRest");
  const repos: RestRepoResponse[] = [];
  for (const repoName of repoNames) {
    const owner = repoName.split("/")[0];
    const repo = repoName.split("/")[1];
    try {
      const result = await gh.rest.repos.get({
        owner: owner,
        repo: repo,
      });
      repos.push(result);
    } catch (err) {
      const httpErr = err as RequestError;
      if (httpErr.status == 404) {
        continue;
      }
      throw err;
    }
  }
  return repos.map((res) => {
    const r = res.data;
    return restRepoDataToFullRepository(r);
  });
}

export async function resolveAllRepos(
  client: GraphQLClient,
  repoNames: string[],
): Promise<Repository[]> {
  let batch: string[] = [];
  const results: Repository[] = [];
  let rateLimit: RateLimit | null = null;

  const retryRequests = async (client: GraphQLClient, names: string[]) => {
    for (let i = 0; i < 5; i++) {
      try {
        const batchResult = await getManyRepos(client, names);
        return batchResult;
      } catch (err) {
        console.log("caught error");
        console.log(err);
        // Hacky retry for now
        await sleep(1000 * i);
      }
    }
    throw new Error("could not get repos after 5 retries");
  };

  const makeRequest = async () => {
    if (rateLimit) {
      if (
        rateLimit.remaining == 0 ||
        rateLimit.remaining - rateLimit.cost <= 0
      ) {
        const timeToReset = Date.parse(rateLimit.resetAt) - Date.now() + 1000;
        await sleep(timeToReset);
      }
    }
    const batchResult = await retryRequests(client, batch);
    rateLimit = batchResult.rateLimit;
    results.push(...batchResult.search.nodes);
  };

  for (const name of repoNames) {
    batch.push(name);

    if (batch.length >= 100) {
      await makeRequest();
      batch = [];
    }
  }
  if (batch.length > 0) {
    await makeRequest();
    batch = [];
  }
  return results;
}
