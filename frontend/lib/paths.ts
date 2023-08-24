/**
 * Joins URI encoded path parts into a string
 * For reference, see https://nextjs.org/docs/app/building-your-application/routing/dynamic-routes#catch-all-segments
 * @param parts comes from a catch-all path from Next.js
 * @returns
 */
export const catchallPathToString = (parts: string[]) => {
  return parts.map((p) => decodeURIComponent(p)).join("/");
};
