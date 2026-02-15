import { PaginationErrors } from "@/app/api/v1/osograph/utils/errors";

export const MAX_PAGE_SIZE = 100;
export const DEFAULT_PAGE_SIZE = 50;

export function encodeCursor(index: number): string {
  return Buffer.from(`cursor:${index}`).toString("base64");
}

export function decodeCursor(cursor: string): number {
  try {
    const decoded = Buffer.from(cursor, "base64").toString("utf-8");
    const match = decoded.match(/^cursor:(\d+)$/);
    if (!match) {
      throw PaginationErrors.invalidCursor();
    }
    return parseInt(match[1], 10);
  } catch {
    throw PaginationErrors.invalidCursor();
  }
}

export interface ConnectionArgs {
  first: number;
  after?: string | null;
}

export interface FilterableConnectionArgs extends ConnectionArgs {
  single?: boolean | null;
  where?: unknown;
}

export function getPaginationParams(args: ConnectionArgs): {
  offset: number;
  limit: number;
} {
  const first = args.first ?? DEFAULT_PAGE_SIZE;
  const offset = args.after ? decodeCursor(args.after) + 1 : 0;

  if (first < 0) {
    throw PaginationErrors.negativePageSize();
  }

  if (first > MAX_PAGE_SIZE) {
    throw PaginationErrors.invalidPageSize(first);
  }

  return {
    offset,
    limit: first,
  };
}

export function getFetchLimit(args: ConnectionArgs): number {
  const { limit } = getPaginationParams(args);
  return limit + 1;
}
