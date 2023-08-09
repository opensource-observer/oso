import { Dayjs } from "dayjs";

// human-readable URL for a package
const getNpmUrl = (slug: string) => `https://www.npmjs.com/package/${slug}`;
// date format used by NPM APIs
const formatDate = (date: Dayjs) => date.format("YYYY-MM-DD");
// combine owner/name into a slug
const getSlug = (owner: string, name: string) => `${owner}/${name}`;

export { formatDate, getNpmUrl, getSlug };
