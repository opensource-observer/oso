import { gql, GraphQLClient } from "graphql-request";
import { unpaginate } from "./unpaginate.js";

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
            url
            name
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

export interface Repository {
  nameWithOwner: string;
  url: string;
  name: string;
  isFork: boolean;
}

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
    // Try getting the information as a user
    const nodes = await unpaginate<UserData>(client)(
      getUserRepos,
      "user.repositories.edges",
      "user.repositories.pageInfo",
      variables,
    );
    return nodes.map((node: any) => node.node);
  }
  //return nodes.map((node: any) => node.node);
}
