import { AppDataSource } from "./data-source.js";
import { Collection } from "./orm-entities.js";

export const CollectionRepository = AppDataSource.getRepository(
  Collection,
).extend({
  // Find any duplicates
  async duplicates() {
    return (await this.manager
      .createQueryBuilder()
      .select()
      .addSelect('lower(c."name")', "name")
      .addSelect('lower(c."slug")', "slug")
      .addSelect('count(c."id")', "count")
      .addSelect('array_agg(c."id")', "ids")
      .addSelect('array_agg(c."name")', "names")
      .from(Collection, "c")
      .groupBy("1,2")
      .having('count(c."id") > 1')
      .getRawMany()) as {
      name: string;
      slug: string;
      count: number;
      ids: number[];
      names: string[];
    }[];
  },
  async nonCanonical() {
    const sumString =
      'SUM(CASE WHEN LOWER(c."slug") = c."slug" THEN 0 ELSE 1 END)';
    return (await this.manager
      .createQueryBuilder()
      .select()
      .addSelect('c."name"', "name")
      .addSelect('c."slug"', "slug")
      .addSelect(sumString, "nonCanonicalCount")
      .from(Collection, "c")
      .groupBy("1,2")
      .having(`${sumString} > 0`)
      .getRawMany()) as {
      name: string;
      slug: string;
      nonCanonicalCount: number;
    }[];
  },
});
