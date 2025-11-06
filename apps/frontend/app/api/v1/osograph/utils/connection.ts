import {
  type ConnectionArgs,
  encodeCursor,
  getPaginationParams,
} from "@/app/api/v1/osograph/utils/pagination";

export interface Edge<T> {
  node: T;
  cursor: string;
}

export interface PageInfo {
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
  endCursor: string | null;
}

export interface Connection<T> {
  edges: Edge<T>[];
  pageInfo: PageInfo;
  totalCount?: number;
}

export function buildConnection<T>(
  nodes: T[],
  args: ConnectionArgs,
  totalCount?: number,
): Connection<T> {
  const { offset, limit } = getPaginationParams(args);

  const hasNextPage = nodes.length > limit;

  const trimmedNodes = hasNextPage ? nodes.slice(0, limit) : nodes;

  const edges: Edge<T>[] = trimmedNodes.map((node, index) => ({
    node,
    cursor: encodeCursor(offset + index),
  }));

  const pageInfo: PageInfo = {
    hasNextPage,
    hasPreviousPage: offset > 0,
    startCursor: edges.length > 0 ? edges[0].cursor : null,
    endCursor: edges.length > 0 ? edges[edges.length - 1].cursor : null,
  };

  return {
    edges,
    pageInfo,
    totalCount,
  };
}

export function getFetchLimit(args: ConnectionArgs): number {
  const { limit } = getPaginationParams(args);
  return limit + 1;
}

export function emptyConnection<T>(): Connection<T> {
  return {
    edges: [],
    pageInfo: {
      hasNextPage: false,
      hasPreviousPage: false,
      startCursor: null,
      endCursor: null,
    },
  };
}
