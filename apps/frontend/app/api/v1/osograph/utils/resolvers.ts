export interface PaginationArgs {
  limit?: number;
  offset?: number;
}

export function getPaginationRange(args: PaginationArgs): [number, number] {
  const offset = args.offset || 0;
  const limit = args.limit || 50;
  return [offset, offset + limit - 1];
}
