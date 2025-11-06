export function encodeCursor(index: number): string {
  return Buffer.from(`cursor:${index}`).toString("base64");
}

export function decodeCursor(cursor: string): number {
  try {
    const decoded = Buffer.from(cursor, "base64").toString("utf-8");
    const match = decoded.match(/^cursor:(\d+)$/);
    if (!match) {
      throw new Error("Invalid cursor format");
    }
    return parseInt(match[1], 10);
  } catch {
    throw new Error("Invalid cursor");
  }
}

export interface ConnectionArgs {
  first?: number;
  after?: string;
}

export function getPaginationParams(args: ConnectionArgs): {
  offset: number;
  limit: number;
} {
  const first = args.first ?? 50;
  const offset = args.after ? decodeCursor(args.after) + 1 : 0;

  if (first < 0) {
    throw new Error("Argument 'first' must be a non-negative integer");
  }

  if (first > 100) {
    throw new Error("Argument 'first' cannot exceed 100");
  }

  return {
    offset,
    limit: first,
  };
}

export function getSupabaseRange(args: ConnectionArgs): [number, number] {
  const { offset, limit } = getPaginationParams(args);
  return [offset, offset + limit - 1];
}

export function getNextCursor(
  currentOffset: number,
  currentLimit: number,
  hasMore: boolean,
): string | null {
  if (!hasMore) {
    return null;
  }
  return encodeCursor(currentOffset + currentLimit - 1);
}

export function hasMoreItems(
  itemCount: number,
  requestedLimit: number,
): boolean {
  return itemCount > requestedLimit;
}

export function getFetchLimit(args: ConnectionArgs): number {
  const { limit } = getPaginationParams(args);
  return limit + 1;
}
